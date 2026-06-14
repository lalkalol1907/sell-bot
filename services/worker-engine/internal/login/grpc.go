package login

import (
	"context"

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

func (s *GRPCServer) requireAuth(ctx context.Context) error {
	return s.validateToken(grpcauth.TokenFromIncoming(ctx))
}

func (s *GRPCServer) validateToken(token string) error {
	if s.internalSecret == "" {
		return nil
	}
	if token != s.internalSecret {
		return errUnauthorized
	}
	return nil
}

var errUnauthorized = &authError{msg: "unauthorized"}

type authError struct{ msg string }

func (e *authError) Error() string { return e.msg }

func (s *GRPCServer) StartLogin(ctx context.Context, req *workerloginpb.StartLoginRequest) (*workerloginpb.LoginStepResponse, error) {
	if err := s.requireAuth(ctx); err != nil {
		return errorResponse("", err)
	}
	step, err := s.mgr.StartLogin(ctx, req.OwnerSellerId, req.Phone)
	if err != nil {
		return errorResponse(step.LoginID, err)
	}
	return toProto(step), nil
}

func (s *GRPCServer) StartQRLogin(ctx context.Context, req *workerloginpb.StartQRLoginRequest) (*workerloginpb.LoginStepResponse, error) {
	if err := s.requireAuth(ctx); err != nil {
		return errorResponse("", err)
	}
	step, err := s.mgr.StartQRLogin(ctx, req.OwnerSellerId)
	if err != nil {
		return errorResponse(step.LoginID, err)
	}
	return toProto(step), nil
}

func (s *GRPCServer) SubmitCode(ctx context.Context, req *workerloginpb.SubmitCodeRequest) (*workerloginpb.LoginStepResponse, error) {
	if err := s.requireAuth(ctx); err != nil {
		return errorResponse(req.LoginId, err)
	}
	step, err := s.mgr.SubmitCode(ctx, req.LoginId, req.Code)
	if err != nil {
		return errorResponse(req.LoginId, err)
	}
	return toProto(step), nil
}

func (s *GRPCServer) SubmitPassword(ctx context.Context, req *workerloginpb.SubmitPasswordRequest) (*workerloginpb.LoginStepResponse, error) {
	if err := s.requireAuth(ctx); err != nil {
		return errorResponse(req.LoginId, err)
	}
	step, err := s.mgr.SubmitPassword(ctx, req.LoginId, req.Password)
	if err != nil {
		return errorResponse(req.LoginId, err)
	}
	return toProto(step), nil
}

func (s *GRPCServer) GetLoginStatus(ctx context.Context, req *workerloginpb.GetLoginStatusRequest) (*workerloginpb.LoginStepResponse, error) {
	if err := s.requireAuth(ctx); err != nil {
		return errorResponse(req.LoginId, err)
	}
	step, err := s.mgr.GetLoginStatus(req.LoginId)
	if err != nil {
		return errorResponse(req.LoginId, err)
	}
	return toProto(step), nil
}

func errorResponse(loginID string, err error) (*workerloginpb.LoginStepResponse, error) {
	return &workerloginpb.LoginStepResponse{
		LoginId: loginID,
		Status:  StatusError,
		Message: err.Error(),
	}, nil
}

func toProto(step Step) *workerloginpb.LoginStepResponse {
	return &workerloginpb.LoginStepResponse{
		LoginId:      step.LoginID,
		Status:       step.Status,
		Message:      step.Message,
		WorkerId:     step.WorkerID,
		QrUrl:        step.QrURL,
		QrExpiresAt:  step.QrExpiresAt,
	}
}
