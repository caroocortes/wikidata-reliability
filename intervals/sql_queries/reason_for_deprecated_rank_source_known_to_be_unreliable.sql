alter table value_change_to_keep
add column reason_for_deprecated_rank_source_known_to_be_unreliable int default 0;

create index idx_statement_qualifier_intervals_qual_property_id on statement_qualifier_intervals(qual_property_id);
create index idx_statement_qualifier_intervals_qual_value on statement_qualifier_intervals(qual_value);
analyze statement_qualifier_intervals;

set work_mem = '4GB';
SET enable_nestloop = off; 
update value_change_to_keep v
set reason_for_deprecated_rank_source_known_to_be_unreliable = 1
from 
	statement_qualifier_intervals sqi
where 
sqi.qual_property_id = 2241 and -- reason for deprecated rank
sqi.qual_value = 'Q22979588' and -- source known to be unreliable
v.entity_id = sqi.entity_id and
v.property_id = sqi.property_id and 
v.value_id = sqi.value_id and
v.change_target = '' and
-- sri.valid_from, v.timestamp, sri.valid_to
v.timestamp >= sqi.valid_from and
v.timestamp < sqi.valid_to -- o <=?
;