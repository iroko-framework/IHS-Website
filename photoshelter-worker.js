/**
 * Cloudflare Worker — PhotoShelter API Proxy
 * Deploy at: api.irokosociety.org  (or ps-proxy.irokosociety.org)
 *
 * Routes:
 *   GET /gallery/:id            → PhotoShelter gallery metadata
 *   GET /gallery/:id/images     → PhotoShelter gallery images
 *
 * All other paths → 404
 */

const API_KEY     = '6_SlIgrqxMg';
const PS_BASE     = 'https://www.photoshelter.com/psapi/v3/mem';
const ALLOWED_ORIGIN = 'https://irokosociety.org';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin':  ALLOWED_ORIGIN,
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age':       '86400',
};

export default {
  async fetch(request, env, ctx) {

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // Only allow GET
    if (request.method !== 'GET') {
      return new Response('Method not allowed', { status: 405, headers: CORS_HEADERS });
    }

    const url      = new URL(request.url);
    const pathname = url.pathname;  // e.g. /gallery/G0000n01IpmZArsk/images

    // Validate path — must match /gallery/{id} or /gallery/{id}/images
    const galleryPath = pathname.match(/^\/gallery\/([^/]+)(\/images)?$/);
    if (!galleryPath) {
      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404,
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' }
      });
    }

    // Forward query params (per_page, page, etc.) plus API key
    const params = new URLSearchParams(url.search);
    params.set('api_key', API_KEY);

    const psUrl = `${PS_BASE}${pathname}?${params.toString()}`;

    // Fetch from PhotoShelter
    let psResponse;
    try {
      psResponse = await fetch(psUrl, {
        headers: { 'Accept': 'application/json' }
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: 'Upstream fetch failed', detail: err.message }), {
        status: 502,
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' }
      });
    }

    // Pass through status + body, add CORS headers
    const body        = await psResponse.text();
    const contentType = psResponse.headers.get('Content-Type') || 'application/json';

    return new Response(body, {
      status: psResponse.status,
      headers: {
        ...CORS_HEADERS,
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=300',  // 5-min cache
      }
    });
  }
};
