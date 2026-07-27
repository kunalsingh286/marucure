package crypto

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"errors"
	"io"
)

// SewadwaarPayload represents the exact JSON structure mandated by the Raj Sewa Dwaar API
type SewadwaarPayload struct {
	Data         string `json:"data"`
	IV           string `json:"iv"`
	EncryptedKey string `json:"encryptedKey"`
}

// StateCryptoEngine handles the official Hybrid AES/RSA Sign-and-Encrypt logic
type StateCryptoEngine struct {
	StatePublicKey *rsa.PublicKey
	LocalPrivateKey *rsa.PrivateKey
}

// LoadStateKeys parses the PEM-encoded keys provided by the environment variables
func LoadStateKeys(pubKeyPEM, privKeyPEM string) (*StateCryptoEngine, error) {
	engine := &StateCryptoEngine{}

	// Parse State Public Key (RSA)
	if pubKeyPEM != "" && pubKeyPEM != "INSERT_STATE_RSA_PUBLIC_KEY_HERE" {
		block, _ := pem.Decode([]byte(pubKeyPEM))
		if block == nil {
			return nil, errors.New("failed to parse state public key PEM block")
		}
		pub, err := x509.ParsePKIXPublicKey(block.Bytes)
		if err != nil {
			return nil, err
		}
		engine.StatePublicKey = pub.(*rsa.PublicKey)
	}

	// Parse Local Private Key (RSA)
	if privKeyPEM != "" && privKeyPEM != "INSERT_LOCAL_RSA_PRIVATE_KEY_HERE" {
		block, _ := pem.Decode([]byte(privKeyPEM))
		if block == nil {
			return nil, errors.New("failed to parse local private key PEM block")
		}
		priv, err := x509.ParsePKCS1PrivateKey(block.Bytes)
		if err != nil {
			return nil, err
		}
		engine.LocalPrivateKey = priv
	}

	return engine, nil
}

// EncryptPayload executes the Hybrid AES-GCM + RSA-OAEP encryption mandated by DoIT&C
func (e *StateCryptoEngine) EncryptPayload(rawJsonPayload []byte) (*SewadwaarPayload, error) {
	if e.StatePublicKey == nil {
		return nil, errors.New("state public key is not loaded, cannot perform encryption")
	}

	// 1. Generate random AES-256 Key
	aesKey := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, aesKey); err != nil {
		return nil, err
	}

	// 2. Encrypt Payload using AES-GCM
	block, err := aes.NewCipher(aesKey)
	if err != nil {
		return nil, err
	}
	aesGCM, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	// Generate random 12-byte IV for GCM
	iv := make([]byte, aesGCM.NonceSize())
	if _, err := io.ReadFull(rand.Reader, iv); err != nil {
		return nil, err
	}

	ciphertext := aesGCM.Seal(nil, iv, rawJsonPayload, nil)

	// 3. Encrypt AES Key using State RSA Public Key (OAEP with SHA-256)
	encryptedAESKey, err := rsa.EncryptOAEP(sha256.New(), rand.Reader, e.StatePublicKey, aesKey, nil)
	if err != nil {
		return nil, err
	}

	// 4. Return the strictly formatted Payload
	return &SewadwaarPayload{
		Data:         base64.StdEncoding.EncodeToString(ciphertext),
		IV:           base64.StdEncoding.EncodeToString(iv),
		EncryptedKey: base64.StdEncoding.EncodeToString(encryptedAESKey),
	}, nil
}
