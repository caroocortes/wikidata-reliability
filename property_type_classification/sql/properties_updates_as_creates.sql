SET enable_nestloop = off; 
create table properties_updates_as_creates as
with values_with_temporal as (
    -- values that EVER carried a temporal qualifier
    select distinct entity_id, property_id, value_id
    from qualifier_change_to_keep
    where qual_property_id in (585, 580) and action = 'CREATE'                 
),
all_values as (
    select distinct entity_id, property_id, value_id
    from small_table  
)
select
    a.property_id,
    count(*)                                   as num_values,
    count(t.value_id)                          as num_values_temporal,
    count(t.value_id)::float / count(*)        as pct_values_temporal_qualifier
from all_values a
left join values_with_temporal t
       using (entity_id, property_id, value_id)
group by a.property_id;


alter table features_property_type_classification
add column updates_as_creates_50 int default 0;

alter table features_property_type_classification
add column updates_as_creates_60 int default 0;

update features_property_type_classification f
set 
	updates_as_creates_50 = case when p.pct_values_temporal_qualifier >= 0.5 then 1 else 0 end,
	updates_as_creates_60 = case when p.pct_values_temporal_qualifier >= 0.6 then 1 else 0 end
from properties_updates_as_creates p
where p.property_id = f.property_id;