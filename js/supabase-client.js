/* =========================================================
   SUPABASE CLIENT
   ========================================================= */

// ⚠️ GANTI DENGAN KREDENSIAL PROJECT ANDA
const SUPABASE_URL = 'https://qcjdstuwlaykxfbltzmp.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_cWIr7SDdd8_yARUgpyS7Gg_GWjBl_78';

window.supabaseClient = window.supabase.createClient(
  SUPABASE_URL,
  SUPABASE_ANON_KEY
);

/* SHA-256 helper */
window.sha256 = async function(text) {
  const enc = new TextEncoder().encode(text);
  const buf = await crypto.subtle.digest('SHA-256', enc);
  return Array.from(new Uint8Array(buf))
    .map(b => b.toString(16).padStart(2, '0')).join('');
};