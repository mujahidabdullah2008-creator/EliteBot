def in_session():
    hour = datetime.now().hour

    morning = (8 <= hour < 12)   # 8AM–12PM
    afternoon = (14 <= hour < 18) # 2PM–6PM

    return morning or afternoon