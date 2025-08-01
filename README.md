# Pseudo-Code Obfuscation Buster
This Python script analyzes and normalizes pseudo-code logic. It detects:
* Redundant conditions
* Contradictory logic
* Variable name typos
* Illogical comparisons (e.g., comparing strings with numbers)
It also converts verbose logic and inconsistent variable naming into clean, standardized expressions.
---

## 📜 Features

* ✅ Normalize logical keywords (`IF`, `AND`, `OR`, `NOT`, etc.)
* 🧠 Detect and flag:

  * Repeated logical conditions
  * Unreachable/contradictory branches
  * Unknown or misspelled variable names
  * Comparisons between mismatched types
* 🪄 Standardize variable naming using a configurable synonym dictionary

---

## 🔧 Usage

```bash
python pseudo_code_obfuscation_buster.py <input_file.txt>
```

Where `<input_file.txt>` contains lines of pseudo-code you want to process.

---

## 💡 Input Example

**Input (`input.txt`):**

```
If UserType is admin AND user_type is admin
If user_status == active THEN do something ELSE IF user_status == active
If userStatuz == ACTIVE
If currentTime == '10' AND itemCount == "5"
```

**Output:**

```
FLAG: Redundant condition 'user_type == admin' in line: If UserType is admin AND user_type is admin
FLAG: Contradictory/unreachable logic in line: If user_status == active THEN do something ELSE IF user_status == active
FLAG: Potential typo(s) in variable name(s): userStatuz in line: If userStatuz == ACTIVE
FLAG: Illogical comparison: Comparing string literal "10" as number, Comparing string literal "5" as number in line: If currentTime == '10' AND itemCount == "5"
```

---

## 🧰 Customization

### 1. **Expand Keyword Normalization**

Update the `LOGIC_KEYWORDS` list to support more logical expressions or synonyms.

### 2. **Add More Variable Synonyms**

Extend the `VAR_SYNONYMS` dictionary to account for other known variable name variations.

---

## 🧠 Implementation Details

* Uses **regex** extensively for pattern detection and normalization.
* Converts all variable names to `snake_case`.
* Catches redundancy by comparing simplified conditions.
* Detects contradictions based on repeated `IF` conditions.
* Flags suspicious tokens that resemble variables but aren't recognized.

---

## 📂 File Structure

```
pseudo_code_obfuscation_buster.py  # Main script
input_file.txt                     # Your pseudo-code input
```

---

## ✅ Requirements

* Python 3.x
* No external libraries required (uses only built-in modules)

---

## 📃 License

This script is free to use and modify for personal, academic, or organizational use.
