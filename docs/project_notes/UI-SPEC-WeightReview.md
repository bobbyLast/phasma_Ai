"""
============================================================
UI SPECIFICATION: Weight Recommendation Review Interface
============================================================

TICKET: UI-001 - Weight Recommendation Review UI
OWNER: Frontend Team + Quant Analytics
ESTIMATE: 5 days
PRIORITY: HIGH
DEPENDENCIES: US-007 (Post-Trade Analytics)

OVERVIEW:
Create a one-page review interface for quant team to evaluate, approve, or reject
weight adjustment recommendations from the post-trade analytics system.

UI REQUIREMENTS:

1. SINGLE PAGE VIEW
- Clean, scannable layout for quick decision making
- All critical information visible without scrolling
- Mobile-responsive for on-call review

2. RECOMMENDATION HEADER
- Recommendation ID and date
- Component name (e.g., "max_slippage_pct")
- Current value → Recommended value
- Confidence score with visual indicator
- Quick approve/reject buttons

3. SUPPORTING EVIDENCE SECTION
- Statistical summary (sample size, p-value, effect size)
- Performance impact projection
- Risk assessment
- A/B test plan preview

4. HISTORICAL CONTEXT
- Last 5 changes for this component
- Performance before/after previous changes
- Trend visualization

5. ACTION PANEL
- Approve with options (immediate, scheduled, A/B test)
- Reject with reason codes
- Request more analysis
- Escalate to senior quant

IMPLEMENTATION SPECIFICATION:

File: frontend/src/components/WeightReviewCard.tsx
```typescript
import React, { useState } from 'react';
import { Card, Button, Badge, Progress, Tabs, Table } from 'antd';
import { Line } from '@ant-design/plots';
import { 
  CheckOutlined, 
  CloseOutlined, 
  ClockCircleOutlined,
  ExclamationCircleOutlined 
} from '@ant-design/icons';

interface WeightRecommendation {
  id: string;
  component: string;
  currentValue: number;
  recommendedValue: number;
  confidence: number;
  reasoning: string;
  supportingMetrics: Record<string, number>;
  statisticalTest: {
    sampleSize: number;
    pValue: number;
    effectSize: number;
    significance: boolean;
  };
  performanceImpact: {
    expectedReturnChange: number;
    riskChange: number;
    sharpeChange: number;
  };
  abTestPlan?: {
    controlAllocation: number;
    testAllocation: number;
    duration: number;
    minTrades: number;
  };
  historicalChanges: Array<{
    date: string;
    oldValue: number;
    newValue: number;
    performance: number;
  }>;
  riskAssessment: {
    level: 'LOW' | 'MEDIUM' | 'HIGH';
    factors: string[];
  };
}

const WeightReviewCard: React.FC<{ recommendation: WeightRecommendation }> = ({ 
  recommendation 
}) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('evidence');

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#52c41a';
    if (confidence >= 0.6) return '#faad14';
    return '#ff4d4f';
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return '#52c41a';
      case 'MEDIUM': return '#faad14';
      case 'HIGH': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };

  const handleApprove = async (options: { immediate?: boolean; abTest?: boolean }) => {
    setLoading(true);
    try {
      const response = await fetch('/api/weights/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recommendationId: recommendation.id,
          ...options
        })
      });
      
      if (response.ok) {
        // Show success notification
      }
    } catch (error) {
      // Show error notification
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (reasonCode: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/weights/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recommendationId: recommendation.id,
          reasonCode
        })
      });
      
      if (response.ok) {
        // Show success notification
      }
    } catch (error) {
      // Show error notification
    } finally {
      setLoading(false);
    }
  };

  const performanceData = recommendation.historicalChanges.map(change => ({
    date: change.date,
    value: change.performance,
    type: 'Performance'
  }));

  return (
    <Card 
      className="weight-review-card"
      title={
        <div className="flex justify-between items-center">
          <div>
            <span className="text-lg font-semibold">
              {recommendation.component}
            </span>
            <div className="text-sm text-gray-500">
              ID: {recommendation.id}
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <Progress 
                percent={recommendation.confidence * 100}
                strokeColor={getConfidenceColor(recommendation.confidence)}
                size="small"
                format={() => `${(recommendation.confidence * 100).toFixed(0)}%`}
              />
              <Badge 
                color={getRiskColor(recommendation.riskAssessment.level)}
                text={recommendation.riskAssessment.level}
              />
            </div>
          </div>
        </div>
      }
      extra={
        <div className="flex gap-2">
          <Button 
            type="primary"
            icon={<CheckOutlined />}
            onClick={() => handleApprove({ immediate: true })}
            loading={loading}
            disabled={recommendation.confidence < 0.6}
          >
            Approve
          </Button>
          <Button 
            icon={<ClockCircleOutlined />}
            onClick={() => handleApprove({ abTest: true })}
            loading={loading}
          >
            A/B Test
          </Button>
          <Button 
            danger
            icon={<CloseOutlined />}
            onClick={() => handleReject('INSUFFICIENT_EVIDENCE')}
            loading={loading}
          >
            Reject
          </Button>
        </div>
      }
    >
      {/* Value Change Display */}
      <div className="mb-4 p-4 bg-gray-50 rounded">
        <div className="flex justify-center items-center gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">
              {recommendation.currentValue.toFixed(4)}
            </div>
            <div className="text-sm text-gray-500">Current</div>
          </div>
          <div className="text-2xl text-gray-400">→</div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {recommendation.recommendedValue.toFixed(4)}
            </div>
            <div className="text-sm text-gray-500">Recommended</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-semibold ${
              (recommendation.recommendedValue - recommendation.currentValue) > 0 
                ? 'text-green-600' 
                : 'text-red-600'
            }`}>
              {((recommendation.recommendedValue - recommendation.currentValue) / 
                recommendation.currentValue * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Change</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <Tabs.TabPane tab="Evidence" key="evidence">
          <div className="space-y-4">
            {/* Reasoning */}
            <div>
              <h4>Reasoning</h4>
              <p className="text-gray-700">{recommendation.reasoning}</p>
            </div>

            {/* Statistical Test */}
            <div>
              <h4>Statistical Evidence</h4>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Sample Size</div>
                  <div className="font-semibold">
                    {recommendation.statisticalTest.sampleSize}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">P-Value</div>
                  <div className="font-semibold">
                    {recommendation.statisticalTest.pValue.toFixed(4)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Effect Size</div>
                  <div className="font-semibold">
                    {recommendation.statisticalTest.effectSize.toFixed(3)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Significant</div>
                  <Badge 
                    status={recommendation.statisticalTest.significance ? 'success' : 'default'}
                    text={recommendation.statisticalTest.significance ? 'Yes' : 'No'}
                  />
                </div>
              </div>
            </div>

            {/* Performance Impact */}
            <div>
              <h4>Expected Performance Impact</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Return Change</div>
                  <div className={`font-semibold ${
                    recommendation.performanceImpact.expectedReturnChange > 0 
                      ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {(recommendation.performanceImpact.expectedReturnChange * 100).toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Risk Change</div>
                  <div className={`font-semibold ${
                    recommendation.performanceImpact.riskChange < 0 
                      ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {(recommendation.performanceImpact.riskChange * 100).toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Sharpe Change</div>
                  <div className={`font-semibold ${
                    recommendation.performanceImpact.sharpeChange > 0 
                      ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {recommendation.performanceImpact.sharpeChange.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>

            {/* Risk Assessment */}
            <div>
              <h4>Risk Assessment</h4>
              <div>
                <Badge 
                  color={getRiskColor(recommendation.riskAssessment.level)}
                  text={recommendation.riskAssessment.level}
                />
                <ul className="mt-2 list-disc list-inside">
                  {recommendation.riskAssessment.factors.map((factor, index) => (
                    <li key={index} className="text-sm text-gray-600">{factor}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="History" key="history">
          <div>
            <h4>Historical Changes</h4>
            <Table 
              dataSource={recommendation.historicalChanges}
              columns={[
                {
                  title: 'Date',
                  dataIndex: 'date',
                  key: 'date'
                },
                {
                  title: 'Old Value',
                  dataIndex: 'oldValue',
                  key: 'oldValue',
                  render: (value) => value.toFixed(4)
                },
                {
                  title: 'New Value',
                  dataIndex: 'newValue',
                  key: 'newValue',
                  render: (value) => value.toFixed(4)
                },
                {
                  title: 'Performance',
                  dataIndex: 'performance',
                  key: 'performance',
                  render: (value) => (
                    <span className={value > 0 ? 'text-green-600' : 'text-red-600'}>
                      {(value * 100).toFixed(2)}%
                    </span>
                  )
                }
              ]}
              pagination={false}
              size="small"
            />
            
            {/* Performance Chart */}
            <div className="mt-4">
              <h4>Performance Trend</h4>
              <Line 
                data={performanceData}
                xField="date"
                yField="value"
                smooth
                color={['#1890ff', '#52c41a']}
              />
            </div>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="A/B Test Plan" key="abtest">
          {recommendation.abTestPlan ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4>Control Allocation</h4>
                  <div className="text-2xl font-semibold">
                    {(recommendation.abTestPlan.controlAllocation * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <h4>Test Allocation</h4>
                  <div className="text-2xl font-semibold text-blue-600">
                    {(recommendation.abTestPlan.testAllocation * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4>Duration</h4>
                  <div className="text-lg">
                    {recommendation.abTestPlan.duration} days
                  </div>
                </div>
                <div>
                  <h4>Min Trades</h4>
                  <div className="text-lg">
                    {recommendation.abTestPlan.minTrades}
                  </div>
                </div>
              </div>

              <div className="p-4 bg-blue-50 rounded">
                <h4>Statistical Power</h4>
                <p className="text-sm text-gray-700">
                  With {recommendation.abTestPlan.minTrades} trades over {recommendation.abTestPlan.duration} days,
                  we have {recommendation.statisticalTest.significance ? 'sufficient' : 'insufficient'} 
                  statistical power to detect the expected effect size.
                </p>
              </div>

              <Button 
                type="primary"
                size="large"
                block
                onClick={() => handleApprove({ abTest: true })}
              >
                Launch A/B Test
              </Button>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              No A/B test plan available for this recommendation
            </div>
          )}
        </Tabs.TabPane>
      </Tabs>

      {/* Supporting Metrics */}
      <div className="mt-4 pt-4 border-t">
        <h4>Supporting Metrics</h4>
        <div className="grid grid-cols-4 gap-2">
          {Object.entries(recommendation.supportingMetrics).map(([key, value]) => (
            <div key={key} className="text-center p-2 bg-gray-50 rounded">
              <div className="text-xs text-gray-500">{key}</div>
              <div className="font-semibold">{value.toFixed(3)}</div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

export default WeightReviewCard;
```

File: frontend/src/pages/WeightReviewDashboard.tsx
```typescript
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Select, DatePicker, Button } from 'antd';
import { FilterOutlined, ReloadOutlined } from '@ant-design/icons';
import WeightReviewCard from '../components/WeightReviewCard';

const WeightReviewDashboard: React.FC = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    component: 'all',
    confidence: 'all',
    risk: 'all',
    dateRange: null
  });

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/weights/recommendations');
      const data = await response.json();
      setRecommendations(data);
      setFiltered(data);
    } catch (error) {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...recommendations];

    if (filters.component !== 'all') {
      filtered = filtered.filter(r => r.component === filters.component);
    }

    if (filters.confidence !== 'all') {
      filtered = filtered.filter(r => {
        if (filters.confidence === 'high') return r.confidence >= 0.8;
        if (filters.confidence === 'medium') return r.confidence >= 0.6 && r.confidence < 0.8;
        if (filters.confidence === 'low') return r.confidence < 0.6;
        return true;
      });
    }

    if (filters.risk !== 'all') {
      filtered = filtered.filter(r => r.riskAssessment.level === filters.risk);
    }

    setFiltered(filtered);
  };

  useEffect(() => {
    applyFilters();
  }, [filters, recommendations]);

  const stats = {
    total: filtered.length,
    highConfidence: filtered.filter(r => r.confidence >= 0.8).length,
    mediumRisk: filtered.filter(r => r.riskAssessment.level === 'MEDIUM').length,
    pendingReview: filtered.filter(r => r.status === 'PENDING').length
  };

  return (
    <div className="weight-review-dashboard">
      {/* Header Stats */}
      <Row gutter={16} className="mb-4">
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Recommendations"
              value={stats.total}
              prefix={<FilterOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="High Confidence"
              value={stats.highConfidence}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Medium Risk"
              value={stats.mediumRisk}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Pending Review"
              value={stats.pendingReview}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card className="mb-4">
        <Row gutter={16} align="middle">
          <Col span={4}>
            <Select
              placeholder="Component"
              value={filters.component}
              onChange={(value) => setFilters({ ...filters, component: value })}
              style={{ width: '100%' }}
            >
              <Select.Option value="all">All Components</Select.Option>
              <Select.Option value="max_slippage_pct">Max Slippage</Select.Option>
              <Select.Option value="insider_signal_weight">Insider Weight</Select.Option>
              <Select.Option value="human_gate_threshold">Human Gate</Select.Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="Confidence"
              value={filters.confidence}
              onChange={(value) => setFilters({ ...filters, confidence: value })}
              style={{ width: '100%' }}
            >
              <Select.Option value="all">All Levels</Select.Option>
              <Select.Option value="high">High (≥80%)</Select.Option>
              <Select.Option value="medium">Medium (60-80%)</Select.Option>
              <Select.Option value="low">Low (<60%)</Select.Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="Risk Level"
              value={filters.risk}
              onChange={(value) => setFilters({ ...filters, risk: value })}
              style={{ width: '100%' }}
            >
              <Select.Option value="all">All Levels</Select.Option>
              <Select.Option value="LOW">Low</Select.Option>
              <Select.Option value="MEDIUM">Medium</Select.Option>
              <Select.Option value="HIGH">High</Select.Option>
            </Select>
          </Col>
          <Col span={4}>
            <DatePicker.RangePicker />
          </Col>
          <Col span={4}>
            <Button 
              icon={<ReloadOutlined />}
              onClick={fetchRecommendations}
              loading={loading}
            >
              Refresh
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Recommendations */}
      <Row gutter={[16, 16]}>
        {filtered.map(recommendation => (
          <Col span={24} key={recommendation.id}>
            <WeightReviewCard recommendation={recommendation} />
          </Col>
        ))}
      </Row>

      {filtered.length === 0 && (
        <Card className="text-center py-8">
          <p className="text-gray-500">No recommendations match current filters</p>
        </Card>
      )}
    </div>
  );
};

export default WeightReviewDashboard;
```

API ENDPOINTS:

File: backend/api/weights.py
```python
from fastapi import APIRouter, Depends, HTTPException
from analytics.post_trade_analytics import PostTradeAnalytics
from typing import List, Dict

router = APIRouter(prefix="/api/weights", tags=["weights"])

@router.get("/recommendations")
async def get_recommendations(
    status: str = "PENDING",
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """Get weight adjustment recommendations"""
    analytics = PostTradeAnalytics(config)
    
    # Fetch from database
    query = """
    SELECT * FROM weight_recommendations 
    WHERE status = %s 
    ORDER BY created_at DESC 
    LIMIT %s OFFSET %s
    """
    
    recommendations = db.execute(query, (status, limit, offset))
    
    return recommendations

@router.post("/approve")
async def approve_recommendation(
    request: ApproveRequest,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Approve a weight recommendation"""
    # Validate permissions
    if not current_user.has_permission('weights.approve'):
        raise HTTPException(403, "Insufficient permissions")
    
    # Record decision
    decision = {
        'recommendation_id': request.recommendationId,
        'decision': 'APPROVE',
        'user_id': current_user.id,
        'timestamp': datetime.now(),
        'options': request.options
    }
    
    db.insert('weight_decisions', decision)
    
    # Apply weight change if immediate
    if request.options.get('immediate'):
        await apply_weight_change(request.recommendationId)
    
    # Setup A/B test if requested
    if request.options.get('abTest'):
        await setup_ab_test(request.recommendationId, request.options)
    
    return {'status': 'approved', 'recommendationId': request.recommendationId}

@router.post("/reject")
async def reject_recommendation(
    request: RejectRequest,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Reject a weight recommendation"""
    if not current_user.has_permission('weights.reject'):
        raise HTTPException(403, "Insufficient permissions")
    
    decision = {
        'recommendation_id': request.recommendationId,
        'decision': 'REJECT',
        'user_id': current_user.id,
        'timestamp': datetime.now(),
        'reason_code': request.reasonCode
    }
    
    db.insert('weight_decisions', decision)
    
    return {'status': 'rejected', 'recommendationId': request.recommendationId}
```

STORYBOOK FOR COMPONENTS:

File: frontend/.storybook/stories/WeightReviewCard.stories.tsx
```typescript
import type { Meta, StoryObj } from '@storybook/react';
import WeightReviewCard from '../components/WeightReviewCard';

const meta: Meta<typeof WeightReviewCard> = {
  title: 'Components/WeightReviewCard',
  component: WeightReviewCard,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const HighConfidence: Story = {
  args: {
    recommendation: {
      id: 'REC-001',
      component: 'max_slippage_pct',
      currentValue: 0.01,
      recommendedValue: 0.012,
      confidence: 0.85,
      reasoning: 'Slippage model error exceeds tolerance',
      statisticalTest: {
        sampleSize: 150,
        pValue: 0.002,
        effectSize: 0.3,
        significance: true
      },
      performanceImpact: {
        expectedReturnChange: 0.02,
        riskChange: -0.01,
        sharpeChange: 0.15
      },
      riskAssessment: {
        level: 'LOW',
        factors: ['Minimal impact on portfolio', 'Backtested over 6 months']
      }
    }
  },
};

export const MediumRisk: Story = {
  args: {
    recommendation: {
      id: 'REC-002',
      component: 'insider_signal_weight',
      currentValue: 0.5,
      recommendedValue: 0.4,
      confidence: 0.7,
      reasoning: 'Signal strength correlation below target',
      statisticalTest: {
        sampleSize: 80,
        pValue: 0.08,
        effectSize: 0.2,
        significance: false
      },
      performanceImpact: {
        expectedReturnChange: -0.01,
        riskChange: 0.00,
        sharpeChange: -0.05
      },
      riskAssessment: {
        level: 'MEDIUM',
        factors: ['May reduce signal capture', 'Limited statistical significance']
      }
    }
  },
};
```

TESTING:

File: frontend/src/components/__tests__/WeightReviewCard.test.tsx
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import WeightReviewCard from '../WeightReviewCard';

describe('WeightReviewCard', () => {
  const mockRecommendation = {
    id: 'TEST-001',
    component: 'max_slippage_pct',
    currentValue: 0.01,
    recommendedValue: 0.012,
    confidence: 0.8,
    reasoning: 'Test reasoning',
    statisticalTest: {
      sampleSize: 100,
      pValue: 0.01,
      effectSize: 0.3,
      significance: true
    },
    performanceImpact: {
      expectedReturnChange: 0.02,
      riskChange: -0.01,
      sharpeChange: 0.1
    },
    riskAssessment: {
      level: 'LOW',
      factors: ['Test factor']
    },
    supportingMetrics: {
      metric1: 0.5,
      metric2: 1.2
    },
    historicalChanges: [],
    abTestPlan: {
      controlAllocation: 0.5,
      testAllocation: 0.5,
      duration: 30,
      minTrades: 100
    }
  };

  it('renders recommendation details correctly', () => {
    render(<WeightReviewCard recommendation={mockRecommendation} />);
    
    expect(screen.getByText('max_slippage_pct')).toBeInTheDocument();
    expect(screen.getByText('0.0100')).toBeInTheDocument();
    expect(screen.getByText('0.0120')).toBeInTheDocument();
    expect(screen.getByText('80%')).toBeInTheDocument();
  });

  it('disables approve button for low confidence', () => {
    const lowConfRec = { ...mockRecommendation, confidence: 0.5 };
    render(<WeightReviewCard recommendation={lowConfRec} />);
    
    const approveButton = screen.getByText('Approve');
    expect(approveButton).toBeDisabled();
  });

  it('calls approve handler when approve clicked', async () => {
    const mockApprove = jest.fn();
    jest.mock('../api/weights', () => ({
      approveRecommendation: mockApprove
    }));
    
    render(<WeightReviewCard recommendation={mockRecommendation} />);
    
    fireEvent.click(screen.getByText('Approve'));
    
    // Expect approve to be called with correct parameters
    await waitFor(() => {
      expect(mockApprove).toHaveBeenCalledWith({
        recommendationId: 'TEST-001',
        immediate: true
      });
    });
  });
});
```

STYLE GUIDELINES:

File: frontend/src/components/WeightReviewCard.module.css
```css
.weight-review-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.weight-review-card .confidence-high {
  color: #52c41a;
}

.weight-review-card .confidence-medium {
  color: #faad14;
}

.weight-review-card .confidence-low {
  color: #ff4d4f;
}

.performance-positive {
  color: #52c41a;
  font-weight: 600;
}

.performance-negative {
  color: #ff4d4f;
  font-weight: 600;
}

.risk-badge-low {
  background-color: #f6ffed;
  border-color: #b7eb8f;
  color: #52c41a;
}

.risk-badge-medium {
  background-color: #fffbe6;
  border-color: #ffe58f;
  color: #faad14;
}

.risk-badge-high {
  background-color: #fff2f0;
  border-color: #ffccc7;
  color: #ff4d4f;
}
```

DEFINITION OF DONE:
- [ ] Component renders correctly
- [ ] All interactions tested
- [ ] API integration working
- [ ] Responsive design
- [ ] Accessibility compliance
- [ ] Performance optimized
- [ ] Error handling complete
- [ ] Documentation updated
- [ ] Code review completed

============================================
END OF UI SPECIFICATION UI-001
============================================
"""
