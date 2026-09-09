alter table value_change_to_keep
add column violates_range_constraint int default 0;

create index idx_range_constraint_min_max_vals on range_constraint(minimum_value, maximum_value);
create index idx_range_constraint_min_val on range_constraint(minimum_value);
create index idx_range_constraint_max_val on range_constraint(maximum_value);
analyze range_constraint;

update value_change_to_keep v
set violates_range_constraint = 1
from range_constraint rc
where 
	rc.property_id = v.property_id and
	(
		-- is not a numeric value
		(new_datatype != 'quantity') or 
		--- it's outside the ranges
		((v.new_value->>0 < minimum_value) or (v.new_value->>0 > maximum_value))
	);