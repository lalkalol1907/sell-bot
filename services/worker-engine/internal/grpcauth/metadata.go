package grpcauth

import (
	"context"

	"google.golang.org/grpc/metadata"
)

const MetadataKey = "x-internal-grpc-token"

func OutgoingContext(ctx context.Context, token string) context.Context {
	if token == "" {
		return ctx
	}
	return metadata.AppendToOutgoingContext(ctx, MetadataKey, token)
}

func TokenFromIncoming(ctx context.Context) string {
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return ""
	}
	vals := md.Get(MetadataKey)
	if len(vals) == 0 {
		return ""
	}
	return vals[0]
}

func IncomingContext(ctx context.Context, token string) context.Context {
	return metadata.NewIncomingContext(ctx, metadata.Pairs(MetadataKey, token))
}
