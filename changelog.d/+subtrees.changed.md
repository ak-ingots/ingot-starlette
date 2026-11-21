`StarletteUnit` mounts two subtrees of its own, each a mount of its own
middleware and errors: `api`, a `StarletteApiUnit` at `/api`, of JSON alone,
refusing an `Accept` of no JSON by 406 and a body not of JSON by 415, its
errors problems of `application/problem+json`; `pages`, a
`StarlettePagesUnit` at the root, of HTML, its errors pages of HTML. The
error policies are shared and tell the problem; a renderer of each subtree,
`StarletteJsonProblemRenderer` or `StarletteHtmlProblemRenderer`, its form.
Its own routes are those of the subtrees; the handlers given by
`add_exception_handler` answer outside them.
