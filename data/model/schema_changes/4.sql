BEGIN;
ALTER TABLE "spam_report" ADD COLUMN reason CHARACTER VARYING;
COMMIT;
