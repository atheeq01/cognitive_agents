-- Enable Row Level Security on the relevant tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE conflicts ENABLE ROW LEVEL SECURITY;

-- Create policies for document isolation
CREATE POLICY project_isolation_documents ON documents
    FOR ALL
    USING (project_id = current_setting('app.project_id', true)::UUID);

-- Create policies for claims isolation
CREATE POLICY project_isolation_claims ON claims
    FOR ALL
    USING (project_id = current_setting('app.project_id', true)::UUID);

-- Create policies for conflicts isolation
CREATE POLICY project_isolation_conflicts ON conflicts
    FOR ALL
    USING (project_id = current_setting('app.project_id', true)::UUID);
