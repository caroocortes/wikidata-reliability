alter table value_change_to_keep
add column current_rank text default null;

set work_mem = '5GB';
SET enable_nestloop = off; 
update value_change_to_keep v
set current_rank = sri.rank
from 
	statement_rank_intervals sri, properties_to_classify ptc
where 
    ptc.property_id = v.property_id and
    v.change_target = '' and
    v.entity_id = sri.entity_id and
    v.property_id = sri.property_id and 
    v.value_id = sri.value_id and
    v.change_target = '' and
    -- sri.valid_from, v.timestamp, sri.valid_to
    v.timestamp >= sri.valid_from and
    (v.timestamp < sri.valid_to or sri.valid_to is null)  -- o <=?
;