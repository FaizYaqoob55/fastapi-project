


def session_remainder_template(user_name:str,session_title:str,session_date:str):
    return (
        f"Hi{user_name},\n\n"
        f"Your growth session\"{session_title}\""
        f"is secheduled on {session_date},\n\n"
        "Regard,\nGrowth App"
    )


def action_item_due_template(user_name:str,action_title:str):
    return (
        f"Hi {user_name},\n\n"
        f"You action item \"{action_title}\"is due,\n\n"
        "Regard,\nGrowth App"
    )


def mention_template(user_name:str, mentioned_by,context):
       return(
            f"Hi {user_name},\n\n"
            f"You were mentioned by {mentioned_by} in a session note: {context}\n\n"
            "Regard,\nGrowth App"
       )

