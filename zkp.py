import random
from config import P, G, SECRET_KEY
import jwt
import datetime

def mod_exp(base, exp, mod):
    return pow(base, exp, mod)

def verify_proof(s, T, C, c, p=29, g=5):
    left_hand_side = mod_exp(g, s, p)
    right_hand_side = (T * mod_exp(C, c, p)) % p
    return left_hand_side == right_hand_side

def challenge_verifier(q):
    return random.randint(1, q - 1)

def issue_token(user_id, node_id):
    token = {
        "user_id": user_id,
        "node_id": node_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
    }
    return token

def verify_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
