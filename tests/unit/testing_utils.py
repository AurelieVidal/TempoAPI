import secrets
import string

def generate_password(
        length=10,
        use_upper=True,
        use_lower=True,
        use_digits=True,
        allow_repetitions=False,
        allow_series=False,
        word=None,
):
    """ Generate a password for tests purposes """
    available_chars = ""
    if use_upper:
        available_chars += string.ascii_uppercase
    if use_lower:
        available_chars += string.ascii_lowercase
    if use_digits:
        available_chars += string.digits

    if not available_chars:
        raise ValueError("At least one character type must be selected.")

    if word:
        if not all(c in available_chars for c in word):
            raise ValueError(
                "Error : unavailable characters"
            )
        length -= len(word)

    def has_series(password):
        for i in range(len(password) - 2):
            if (
                (ord(password[i + 1]) - ord(password[i]) == 1) and
                (ord(password[i + 2]) - ord(password[i + 1]) == 1)
            ):
                return True
        return False

    def has_repetitions(password):
        return (
            any(password[i] == password[i + 1] == password[i + 2]
                for i in range(len(password) - 2))
        )

    password = ""

    while not password or \
            (allow_series and not has_series(password)) or \
            (allow_repetitions and not has_repetitions(password)) or \
            (not allow_series and has_series(password)) or \
            (not allow_repetitions and has_repetitions(password)):

        password = []

        if use_upper:
            password.append(secrets.choice(string.ascii_uppercase))
        if use_lower:
            password.append(secrets.choice(string.ascii_lowercase))
        if use_digits:
            password.append(secrets.choice(string.digits))

        while len(password) < length:
            password.append(secrets.choice(available_chars))

        if word:
            password.append(word)

        password = ''.join(password)

    if not allow_repetitions:
        while has_repetitions(password):
            password = (
                ''
                .join(secrets.choice(available_chars) for _ in range(length))
            )

    if not allow_series:
        while has_series(password):
            password = (
                ''
                .join(secrets.choice(available_chars) for _ in range(length))
            )

    return password
