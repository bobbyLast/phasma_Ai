"""
Engineering Ticket: Canonical Entity Resolution
============================================

TICKET: US-002 - Wire Canonical Entity Graph into Form 4 Pipeline

OVERVIEW:
Ensure all filings map to canonical company_id, including trusts, subsidiaries,
and related persons. Prevent missed buys due to entity fragmentation.

ACCEPTANCE CRITERIA:
1. Entity graph maps subsidiaries/related entities to parent
2. Form 4 parser resolves filing entity to canonical company_id
3. Historical filings reprocessed with entity mapping
4. Aggregation correctly combines buys across related entities
5. Audit trail shows entity resolution for each filing

IMPLEMENTATION DETAILS:
- Build entity graph from SEC relationships
- Add entity resolution to _parse_form4_transactions()
- Update aggregation to use canonical company_id
- Batch reprocess historical data
- Add entity_mapping to provenance

DATA STRUCTURES:
```python
entity_graph = {
    'AAPL': {
        'canonical_id': 'AAPL',
        'subsidiaries': ['BREK', 'BRK'],
        'trusts': ['AAPL TRUST'],
        'related_officers': ['JOHN_DOE_TRUST']
    }
}
```

UNIT TESTS:
```python
def test_subsidiary_mapping():
    # Given: Buy filed under subsidiary
    # When: Entity resolution applied
    # Then: Buy aggregated to parent
    
def test_trust_mapping():
    # Given: Buy filed under trust
    # When: Entity resolution applied
    # Then: Buy counted for insider conviction
```

INTEGRATION TEST:
- Feed known subsidiary filings
- Verify aggregation includes them
- Check audit shows entity mapping

ESTIMATE: 5 days
PRIORITY: HIGH
DEPENDENCIES: SEC entity data source
"""
