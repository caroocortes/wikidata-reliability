alter table value_change_to_keep
add column has_reference int default 0;

set work_mem = '5GB';
SET enable_nestloop = off; 
update value_change_to_keep v
set has_reference = 1
from 
	statement_reference_intervals sri
where 
v.entity_id = sri.entity_id and
v.property_id = sri.property_id and 
v.value_id = sri.value_id and
v.change_target = '' and
-- sri.valid_from, v.timestamp, sri.valid_to
v.timestamp >= sri.valid_from and
v.timestamp < sri.valid_to -- o <=?
;
