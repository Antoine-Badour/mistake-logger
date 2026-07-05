const DEFAULT_SUPABASE_URL = 'https://prjkktsdmvbmdqduvqzz.supabase.co';
const DEFAULT_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByamtrdHNkbXZibWRxZHV2cXp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMyNDAzNjAsImV4cCI6MjA5ODgxNjM2MH0.Fxa2UoeUhQMDpt_HqeFLeBB-BLqXuTAOeqlYupsx-0M';

module.exports = (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.status(200).json({
    supabaseUrl: process.env.SUPABASE_URL || DEFAULT_SUPABASE_URL,
    supabaseAnonKey: process.env.SUPABASE_ANON_KEY || DEFAULT_SUPABASE_ANON_KEY
  });
};
