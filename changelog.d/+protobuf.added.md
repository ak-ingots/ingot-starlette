Added the transcoding of the services of protobuf to HTTP, by the extra
`protobuf` (protobuf and googleapis-common-protos, no grpcio):
`BaseStarletteProtobufEndpoint` routes each method of
`StarletteProtobufRpc` its addon gives by the annotation `google.api.http`
of its contract (AIP-127), the request and the reply the canonical JSON of
proto3 of their messages, the body `*`, the variables of the path and the
query; a request not of its message is refused by 400, a rule it does not
transcode, a stream or a method of no rule fail the start. `get_http_status`
gives the status of HTTP of a code of `google.rpc` (AIP-193).
