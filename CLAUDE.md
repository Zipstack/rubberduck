Remember that the basic idea for this project is in prompting/idea.md, the spec is in prompting/spec.md and the prompt plan, which serves as the implementation plan is in prompting/prompt_plan.md. Always read these files to get a good idea about how the implementation is to be carried out. Also, remember that after the implementation, tests need to be written and run successfully before moving on to the next step. Once a step has been implemented, always mark it as done in the prompting/prompt_plan.md file.

## Default User Credentials

A default user is automatically created on first startup if no users exist in the database:

- **Email**: admin@rubberduck.local
- **Password**: admin

This allows immediate access to the application without requiring registration. The default user has the same capabilities as any other user and can create and manage proxy instances.

## AWS Bedrock Proxy Support

✅ **COMPLETED**: AWS Bedrock proxy implementation with dual-mode authentication:

### Custom Headers Mode (Recommended)
- Use `X-AWS-Access-Key` and `X-AWS-Secret-Key` headers
- Proxy re-signs requests with client credentials
- Full caching, error injection, and logging support
- Test with: `python test_bedrock_unsigned.py`

### Endpoint Override Mode (Limited)  
- Use boto3 with `endpoint_url='http://localhost:8009'`
- Limited by AWS SigV4 signature mismatch issues
- Test with: `python test_bedrock_proxy_aware.py`

### Documentation
- Complete implementation guide: `BEDROCK_PROXY_GUIDE.md`
- Error testing: `python test_bedrock_errors.py`
- Cache testing: `python test_bedrock_caching.py`

**Key Insight**: FastAPI cannot implement traditional HTTP CONNECT proxies due to lack of CONNECT method support. Our API reverse proxy approach provides full functionality for LLM use cases.

## Notes

- For Rubberduck, use the venv in the project root. For the testing script, use the venv at @scripts/proxy_testing/. Do not use the system Python.
- Do not start the backend or frontend servers yourself. I will run them with stdout and stderr redirected to <project_root>/backend.log and <project_root>/frontend/frontend.log. You can read these files to understand what's going on.
- Whenever the user asks you to commit / push to git, always do it from the project's root directory and never commit or push without first confirming with me.
- The Django backend listens on port 9000, while the frontend listens on port 5173.
