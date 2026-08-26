export default {
  async fetch(request, env) {
    // foodlaw.ai and www.foodlaw.ai are served by this site.
    // supplemental.pl is a separate site; do not redirect between them.
    return env.ASSETS.fetch(request);
  },
};
