package main

import (
	"context"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"github.com/sellbot/worker-engine/internal/config"
	"github.com/sellbot/worker-engine/internal/core"
	"github.com/sellbot/worker-engine/internal/login"
	"github.com/sellbot/worker-engine/internal/manager"
	"github.com/sellbot/worker-engine/internal/publisher"
	workerloginpb "github.com/sellbot/worker-engine/internal/gen/workerlogin"
	"google.golang.org/grpc"
)

func startLoginGRPC(port string, srv workerloginpb.WorkerLoginServiceServer) {
	lis, err := net.Listen("tcp", ":"+port)
	if err != nil {
		log.Printf("login grpc listen failed: %v", err)
		return
	}
	grpcSrv := grpc.NewServer()
	workerloginpb.RegisterWorkerLoginServiceServer(grpcSrv, srv)
	log.Printf("login gRPC on :%s", port)
	go func() {
		if err := grpcSrv.Serve(lis); err != nil {
			log.Printf("login grpc serve: %v", err)
		}
	}()
}

func main() {
	cfg := config.Load()
	log.Printf("worker-engine starting (core=%s)", cfg.CoreGRPCAddr)

	natsPub, err := publisher.Connect(cfg.NatsURL)
	if err != nil {
		log.Fatalf("nats connect: %v", err)
	}
	defer natsPub.Close()

	if cfg.DevInjectMessage != "" {
		_ = natsPub.PublishDevMessage(cfg.OwnerSellerID, cfg.WorkerID, cfg.DevInjectMessage, 1001, 999001, "Тестовый чат", "test_user")
	}

	coreClient, err := core.NewClient(cfg.CoreGRPCAddr, cfg.InternalGRPCSecret)
	if err != nil {
		log.Printf("core client failed: %v", err)
	}

	loginMgr := login.NewManager(cfg.TgAPIID, cfg.TgAPIHash, cfg.SessionEncryptionKey, coreClient)
	startLoginGRPC(envOr("LOGIN_GRPC_PORT", "50053"), login.NewGRPCServer(loginMgr, cfg.InternalGRPCSecret))

	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	if coreClient != nil {
		defer coreClient.Close()
		mgr := manager.New(cfg, coreClient, natsPub)
		go func() {
			if err := mgr.Start(ctx); err != nil {
				log.Printf("manager exit: %v", err)
			}
		}()
	}

	<-ctx.Done()
	log.Println("worker-engine shutting down")
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func init() {
	log.SetOutput(os.Stdout)
	log.SetFlags(log.LstdFlags | log.Lmsgprefix)
	log.SetPrefix("[worker-engine] ")
}
