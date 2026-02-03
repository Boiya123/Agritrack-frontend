# Fabric Gateway SDK Installation

To use the Hyperledger Fabric integration, install the required dependency:

```bash
pip install fabric-gateway
```

## Full Requirements

Add to your `requirements.txt`:

```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
pyjwt==2.8.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pytz==2023.3

# Hyperledger Fabric
fabric-gateway>=1.2.0
grpcio>=1.60.0
```
