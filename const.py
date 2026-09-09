WD_STRING_TYPES = ['monolingualtext', 'string', 'external-id', 'url', 'commonsMedia', 'geo-shape', 'tabular-data', 'math', 'musical-notation', 'unknown-values']
WD_ENTITY_TYPES = ['wikibase-item', 'wikibase-entityid', 'wikibase-property', 'wikibase-lexeme', 'wikibase-sense', 'wikibase-form', 'entity-schema']

# added space in front of fix to remove words that have fix on them (e.g., prefix, suffix)
GOOD_COMMENT_KEYWORDS = [' fix', 'correct', 'improve', 'repair', 'clean', 'error', 'wrong', 'mistake']

BASE_COLS = ['timestamp', 'revision_id', 'entity_id', 'entity_label', 'property_id', 'property_label', 'value_id', 
                 'old_value', 'new_value', 'old_value_label', 'new_value_label', 'action', 'user_id', 'username', 'comment', 
                 'old_datatype', 'new_datatype', 'change_type', 'label']

CHANGE_TYPE_DEFINITIONS = """
property_value_update — value replaced with a semantically different one (e.g. corrections, real-world updates, sign changes) \n
refinement — value replaced with a more specific/precise one, same meaning (e.g. adding decimal precision, narrowing a classification, adding date detail) \n
unrefinement — value replaced with a less specific/precise one, same meaning (e.g. removing decimal precision, broadening a classification) \n
re_formatting — surface-level representation change, no meaning change (e.g. trailing zeros, capitalization, spacing) \n
textual_change — text corrected for language errors without changing meaning (e.g. typo/spelling/grammar fix) \n
link_change — entity reference replaced by one with similar label but different concept (e.g. "Victoria" the person -> "Victoria" the place) \n
is_reverted - a change reverted by a subsequent change \n
reversion - the change doing a revert of a previous change \n
"""


SANDBOX_ENTITIES = [4115189, 112795079, 15397819, 13406268, 17339402, 16943273]
