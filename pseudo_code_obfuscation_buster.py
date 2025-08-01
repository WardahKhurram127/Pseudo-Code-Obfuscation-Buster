import re
import sys
from collections import defaultdict

# --- Normalization Dictionaries ---
LOGIC_KEYWORDS = [
    (r"\b(IF|WHENEVER|PROVIDED THAT|ONLY WHEN)\b", "IF"),
    (r"\b(AND|ALSO|IN ADDITION TO)\b", "AND"),
    (r"\b(OR|EITHER|UNLESS)\b", "OR"),
    (r"\b(NOT|IS NOT|DIFFERENT FROM)\b", "NOT"),
    (r"\b(EQUALS|IS SAME AS|MATCHES)\b", "=="),
    (r"\b(GREATER THAN|ABOVE)\b", ">"),
    (r"\b(LESS THAN|BELOW)\b", "<"),
    (r"\b(TRUE|YES|ACTIVE)\b", "TRUE"),
    (r"\b(FALSE|NO|INACTIVE)\b", "FALSE"),
    (r"\b(IS)\b", "=="),  # IS as equality unless followed by NOT
]

# Variable normalization map (add more as needed)
VAR_SYNONYMS = {
    "user_type": ["UserType", "user_type", "type_of_user", "User_Type", "uset_type"],
    "account_status": ["ACCT_STATUS", "accountStatus", "status_of_account", "Acct_Status", "account_status"],
    "customer_tier": ["Customer_Tier", "customerTier", "tier_of_customer", "customer_tier"],
    "purchase_amount": ["purchaseAmount", "amount_of_purchase", "purchase_amount"],
    "user_id": ["user_ID", "UserId", "userId", "user_id", "ID_of_user"],
    "current_time": ["current_TIME", "CurrentTime", "currentTime", "current_time", "time_now"],
    "user_role": ["User_Role", "user_role", "role_of_user", "userRole"],
    "item_count": ["itemCount", "Item_Count", "count_of_items", "item_count"],
    "item_weight": ["item_weight", "ItemWeight", "weight_of_item", "itemWeight"],
    "customer_rating": ["customer_rating", "CustomerRating", "rating_of_customer", "customerRating"],
    "user_status": ["user_status", "UserStatus", "status_of_user", "userStatus"],
    "is_user_admin": ["is_User_Admin", "is_user_admin", "isAdmin", "IsUserAdmin"],
}

# Reverse map for typo detection
ALL_VAR_NAMES = set()
VAR_CANONICAL = dict()
for canon, syns in VAR_SYNONYMS.items():
    for s in syns:
        ALL_VAR_NAMES.add(s.lower())
        VAR_CANONICAL[s.lower()] = canon

# Helper: snake_case conversion
def to_snake_case(s):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"[\s\-]+", "_", s)
    return s.lower()

# Helper: variable normalization
def normalize_var(var):
    v = var.strip().replace("'", "").replace('"', "")
    v_snake = to_snake_case(v)
    # Try canonical mapping
    for canon, syns in VAR_SYNONYMS.items():
        if v in syns or v_snake in syns or v.lower() in [x.lower() for x in syns]:
            return canon
    return v_snake

# Helper: keyword normalization
def normalize_keywords(line):
    # IS NOT must be replaced before IS
    line = re.sub(r"\bIS NOT\b", "NOT", line, flags=re.IGNORECASE)
    for pat, repl in LOGIC_KEYWORDS:
        line = re.sub(pat, repl, line, flags=re.IGNORECASE)
    return line

# Helper: variable/parameter normalization in line
def normalize_variables(line):
    # Find all likely variable names (before ==, !=, >, <, etc.)
    var_pattern = re.compile(r"([a-zA-Z_][a-zA-Z0-9_\- ]*)\s*(==|!=|>|<|AND|OR|NOT)")
    matches = var_pattern.findall(line)
    for m in matches:
        orig = m[0]
        norm = normalize_var(orig)
        if orig != norm:
            line = re.sub(rf"\b{re.escape(orig)}\b", norm, line)
    # Also handle variables in IS/==/!=/etc. expressions
    for canon, syns in VAR_SYNONYMS.items():
        for s in syns:
            if s != canon:
                line = re.sub(rf"\b{re.escape(s)}\b", canon, line, flags=re.IGNORECASE)
    return line

# Helper: literal normalization (TRUE/FALSE)
def normalize_literals(line):
    line = re.sub(r'==\s*TRUE', '== TRUE', line, flags=re.IGNORECASE)
    line = re.sub(r'==\s*FALSE', '== FALSE', line, flags=re.IGNORECASE)
    return line

# Helper: Redundancy and contradiction detection
def detect_redundancy(line):
    # Find all conditions (split by AND/OR, ignore parentheses for now)
    conds = re.split(r'\bAND\b|\bOR\b', line)
    conds = [c.strip() for c in conds if c.strip()]
    seen = set()
    redundants = []
    for c in conds:
        # Remove THEN/DO/ELSE etc. for comparison
        c_clean = re.sub(r'\b(THEN|DO|ELSE)\b.*', '', c).strip()
        if c_clean in seen:
            redundants.append(c_clean)
        else:
            seen.add(c_clean)
    return redundants

def detect_contradiction(line):
    # Look for IF x == y ... ELSE IF x == y ...
    contradiction = re.search(r'IF (.+?) == (.+?) (THEN|DO).+ELSE IF \1 == \2', line)
    if contradiction:
        return True
    return False

def detect_typos(line):
    # Find all variable-like tokens
    tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', line)
    typos = []
    for t in tokens:
        t_l = t.lower()
        if t_l not in ALL_VAR_NAMES and t_l not in VAR_CANONICAL:
            # Heuristic: if it's not a known var, and looks like a var, flag
            if len(t) > 4 and not t.isupper() and not t.islower():
                typos.append(t)
    return typos

def detect_illogical(line):
    # Look for string == number or number == string
    illogical = []
    pattern = re.compile(r'(\w+)\s*(==|!=|>|<)\s*([\'\"]?)([\w\s]+)\3')
    for m in pattern.finditer(line):
        var, op, quote, val = m.groups()
        if quote:
            # val is string
            if val.strip().isdigit():
                illogical.append(f'Comparing string literal "{val}" as number')
        else:
            # val is not quoted
            if not val.strip().isdigit():
                illogical.append(f'Comparing unquoted value {val} as string')
    return illogical

# Main processing function
def process_line(line):
    orig_line = line.strip()
    line = normalize_keywords(orig_line)
    line = normalize_variables(line)
    line = normalize_literals(line)
    # Redundancy
    redundants = detect_redundancy(line)
    # Contradiction
    contradiction = detect_contradiction(line)
    # Typos
    typos = detect_typos(line)
    # Illogical
    illogical = detect_illogical(line)
    # Output
    output = []
    if redundants:
        output.append(f"FLAG: Redundant condition '{redundants[0]}' in line: {orig_line}")
    elif contradiction:
        output.append(f"FLAG: Contradictory/unreachable logic in line: {orig_line}")
    elif typos:
        output.append(f"FLAG: Potential typo(s) in variable name(s): {', '.join(typos)} in line: {orig_line}")
    elif illogical:
        output.append(f"FLAG: Illogical comparison: {', '.join(illogical)} in line: {orig_line}")
    else:
        output.append(line)
    return output

# Main entry point
def main():
    if len(sys.argv) < 2:
        print("Usage: python pseudo_code_obfuscation_buster.py <input_file.txt>")
        sys.exit(1)
    infile = sys.argv[1]
    with open(infile, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            for out in process_line(line):
                print(out)

if __name__ == "__main__":
    main()