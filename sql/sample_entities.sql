
-- 50 entities per property that are not one of WD's defined sandboxes
create table sampled_entities_irregular as
select entity_id, property_id
from (
    select 
        entity_id, property_id,
        row_number() over (
            partition by property_id 
            order by random()
        ) as rn
    from entities_irregular_props
    where entity_id not in (4115189, 112795079, 15397819, 13406268, 17339402, 16943273)
) t
where rn <= 50;

create table sampled_entities_static as
select entity_id, property_id
from (
    select 
        entity_id, property_id,
        row_number() over (
            partition by property_id 
            order by random()
        ) as rn
    from entities_static_props
    where entity_id not in (4115189, 112795079, 15397819, 13406268, 17339402, 16943273)
) t
where rn <= 50;
