package cloud

import (
	"context"
	"bytes"
	"fmt"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type SDCStorageEngine struct {
	S3Client *s3.Client
	Bucket   string
}

func InitializeSDCBucket() (*SDCStorageEngine, error) {
	// Point to internal SDC Endpoint URL blocks or private MinIO container setups
	cfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithRegion("us-east-1"),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider("SDC_ACCESS_KEY_ID", "SDC_SECRET_ACCESS_KEY", "")),
		config.WithEndpointResolverWithOptions(aws.EndpointResolverWithOptionsFunc(
			func(service, region string, options ...interface{}) (aws.Endpoint, error) {
				return aws.Endpoint{
					URL: "https://sdc-storage.rajasthan.gov.in",
				}, nil
			},
		)),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to mount config drivers: %w", err)
	}

	return &SDCStorageEngine{
		S3Client: s3.NewFromConfig(cfg),
		Bucket:   "marucure-diagnostic-blobs",
	}, nil
}

func (s *SDCStorageEngine) UploadXrayPayload(ctx context.Context, screeningID string, rawBinaryData []byte) (string, error) {
	_, err := s.S3Client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:      &s.Bucket,
		Key:         &screeningID,
		Body:        bytes.NewReader(rawBinaryData),
		ContentType: aws.String("image/png"),
	})
	if err != nil {
		return "", fmt.Errorf("cloud ingestion failed: %w", err)
	}

	return fmt.Sprintf("https://sdc-storage.rajasthan.gov.in/marucure-diagnostic-blobs/%s", screeningID), nil
}
