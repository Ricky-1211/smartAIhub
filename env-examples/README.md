# Environment Variables Examples

This directory contains `.env.example` files for all services.

## How to Use

1. **For Root Configuration (Docker Compose):**
   ```bash
   cp env-examples/root.env.example .env
   # Edit .env with your values
   ```

2. **For Individual Services:**
   ```bash
   # Example for auth-service
   cp env-examples/auth-service.env.example auth-service/.env
   # Edit auth-service/.env with your values
   ```

## Available Example Files

- `root.env.example` - Main configuration for Docker Compose
- `auth-service.env.example` - Authentication service
- `gateway.env.example` - API Gateway
- `spam-detection.env.example` - Spam detection service
- `whatsapp-analysis.env.example` - WhatsApp analysis service
- `movie-recommendation.env.example` - Movie recommendation service
- `resume-matcher.env.example` - Resume matcher service
- `house-price-prediction.env.example` - House price prediction service
- `fraud-detection.env.example` - Fraud detection service
- `code-review.env.example` - Code review service
- `logging-service.env.example` - Logging service
- `search-service.env.example` - Search service
- `model-management.env.example` - Model management service
- `frontend.env.example` - Frontend application

## Important Notes

- **Never commit `.env` files to Git** - they contain sensitive information
- Always copy from `.env.example` files, don't create from scratch
- Change all default passwords and secrets in production
- See `ENV_SETUP.md` in the root directory for detailed documentation

