package login

import (
	"context"
	"fmt"

	workerloginpb "github.com/sellbot/worker-engine/internal/gen/workerlogin"
	"github.com/sellbot/worker-engine/internal/grpcauth"
)

type GRPCServer struct {
	workerloginpb.UnimplementedWorkerLoginServiceServer
	mgr            *Manager
	internalSecret string
}

func NewGRPCServer(mgr *Manager, internalSecret string) *GRPCServer {
	return &GRPCServer{mgr: mgr, internalSecret: internalSecret}
}

func (s *GRPCServer) validateToken(token string) error {
	if s.internalSecret == "" {
		return nil
	}
	if token != s.internalSecret {
		return fmt.Errorf("unauthorized")
	}
	return nil
}

func (s *GRPCServer) StartLogin(ctx context.Context, req *workerloginpb.StartLoginRequest) (*workerloginpb.LoginStepResponse, error) {
	if err := s.validateToken(grpcauth.TokenFromIncoming(ctx)); err != nil {
		return &workerloginpb.LoginStepResponse{Status: StatusError, Message: err.Error()}, nil
	}
	step, err := s.mgr.StartLogin(ctx, req.OwnerSellerId, req.Phone)
	if err != nil {
		return &workerloginpb.LoginStepResponse{
			Status:  StatusError,
			Message: err.Error(),
		}, nil
	}
	return toProto(step), nil
}

func (s *GRPCServer) SubmitCode(ctx context.Context, req *workerloginpb.SubmitCodeRequest) (*workerloginpb.LoginStepResponse, error) {
	step, err := s.mgr.SubmitCode(ctx, req.LoginId, req.Code)
	if err != nil {
		return &workerloginpb.LoginStepResponse{
			LoginId: req.LoginId,
			Status:  StatusError,
			Message: err.Error(),
		}, nil
	}
	return toProto(step), nil
}

func (s *GRPCServer) SubmitPassword(ctx context.Context, req *workerloginpb.SubmitPasswordRequest) (*workerloginpb.LoginStepResponse, error) {
	step, err := s.mgr.SubmitPassword(ctx, req.LoginId, req.Password)
	if err != nil {
		return &workerloginpb.LoginStepResponse{
			LoginId: req.LoginId,
			Status:  StatusError,
			Message: err.Error(),
		}, nil
	}
	return toProto(step), nil
}

func toProto(step Step) *workerloginpb.LoginStepResponse {
	return &workerloginpb.LoginStepResponse{
		LoginId:  step.LoginID,
		Status:   step.Status,
		Message:  step.Message,
		WorkerId: step.WorkerID,
	}
}
