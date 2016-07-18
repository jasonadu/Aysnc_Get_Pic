
drop table if exists detail;
CREATE TABLE detail (jobname VARCHAR NOT NULL, itemurl VARCHAR NOT NULL);

drop table if exists job;
CREATE TABLE job (username VARCHAR NOT NULL, jobname VARCHAR NOT NULL, status INT);
