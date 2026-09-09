create table update_comments as 
select r.revision_id, r.comment
from value_change v join revision r on r.revision_id = v.revision_id
where action = 'UPDATE' and change_target = ''
group by r.revision_id, r.comment;

delete 
from update_comments
where comment = '';

update update_comments
set cleaned_comment = REGEXP_REPLACE(comment, '/\*.*?\*/', '');

select *
from update_comments
where 
	cleaned_comment ilike 
	ANY(ARRAY['% fix%', '% correct%', '% improve%', '% repair%', '% error%', '% wrong%', '% mistake%', '% clean%']);