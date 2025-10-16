"""
HTML response templates for OAuth callbacks (DEiD).
Modern dark theme style, using Inter font and solid color palette.
"""

from typing import Optional


def get_oauth_success_template(
    platform: str, username: str, account_id: str, status: str, signature: str
) -> str:
    """
    Generate HTML template for successful OAuth verification.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{platform.title()} Verification Success - DEiD</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000000;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            color: #FFFFFF;
        }}

        .container {{
            width: 100%;
            max-width: 1200px;
            text-align: center;
            animation: fadeIn 0.6s ease-out;
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .logo {{
            width: 200px;
            height: 200px;
            margin: 0 auto 3rem;
            display: block;
        }}

        h1 {{
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            color: #FFFFFF;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .subtitle {{
            font-size: 1rem;
            font-weight: 500;
            color: #A0A0A0;
            line-height: 1.6;
            margin-bottom: 2rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .closing-message {{
            font-size: 0.875rem;
            font-weight: 500;
            color: #666666;
            margin-top: 2rem;
            letter-spacing: 0.05em;
        }}

        @media (max-width: 640px) {{
            .logo {{
                width: 150px;
                height: 150px;
                margin-bottom: 2rem;
            }}

            h1 {{
                font-size: 2rem;
            }}

            .subtitle {{
                font-size: 0.875rem;
                margin-bottom: 1.5rem;
            }}

            .closing-message {{
                font-size: 0.75rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="/deid_logo_noname.png" alt="DEiD Logo" class="logo">
        <h1>{platform.title()} Verification Success</h1>
        <p class="subtitle">
            Your {platform.title()} account has been successfully verified and linked to your DEiD profile.
        </p>
        <p class="closing-message">
            This window will close automatically in <span id="countdown">5</span> seconds...
        </p>
    </div>

    <script>
        // Countdown timer
        let seconds = 5;
        const countdownElement = document.getElementById('countdown');

        const interval = setInterval(() => {{
            seconds--;
            countdownElement.textContent = seconds;
            if (seconds <= 0) {{
                clearInterval(interval);
            }}
        }}, 1000);

        // Auto-close after 5 seconds
        setTimeout(() => {{
            window.close();
        }}, 5000);
    </script>
</body>
</html>
"""


def get_oauth_error_template(
    platform: str, error_message: str, status_code: Optional[int] = None
) -> str:
    """
    Generate HTML template for OAuth verification error.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{platform.title()} Verification Failed - DEiD</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000000;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            color: #FFFFFF;
        }}

        .container {{
            width: 100%;
            max-width: 1200px;
            text-align: center;
            animation: fadeIn 0.6s ease-out;
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .logo {{
            width: 200px;
            height: 200px;
            margin: 0 auto 3rem;
            display: block;
        }}

        h1 {{
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            color: #FFFFFF;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .subtitle {{
            font-size: 1rem;
            font-weight: 500;
            color: #A0A0A0;
            line-height: 1.6;
            margin-bottom: 3rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .return-button {{
            background: linear-gradient(135deg, #EF4444, #F87171);
            color: #000000;
            border: none;
            border-radius: 3rem;
            padding: 1.25rem 3rem;
            font-size: 1.125rem;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
        }}

        .return-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(239, 68, 68, 0.5);
        }}

        .return-button:active {{
            transform: translateY(0);
        }}

        @media (max-width: 640px) {{
            .logo {{
                width: 150px;
                height: 150px;
                margin-bottom: 2rem;
            }}

            h1 {{
                font-size: 2rem;
            }}

            .subtitle {{
                font-size: 0.875rem;
                margin-bottom: 2rem;
            }}

            .return-button {{
                padding: 1rem 2.5rem;
                font-size: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="/deid_logo_noname.png" alt="DEiD Logo" class="logo">
        <h1>{platform.title()} Verification Failed</h1>
        <p class="subtitle">
            {error_message}
        </p>
        <a href="javascript:window.close()" class="return-button">
            Return to DEiD
        </a>
    </div>

    <script>
        // Auto-close after 8 seconds
        setTimeout(() => {{
            window.close();
        }}, 8000);
    </script>
</body>
</html>
"""


def get_oauth_already_linked_template(
    platform: str, username: str, account_id: str, status: str
) -> str:
    """
    Generate HTML template for already linked OAuth account.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Already Linked - DEiD</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000000;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            color: #FFFFFF;
        }}

        .container {{
            width: 100%;
            max-width: 1200px;
            text-align: center;
            animation: fadeIn 0.6s ease-out;
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .logo {{
            width: 200px;
            height: 200px;
            margin: 0 auto 3rem;
            display: block;
        }}

        h1 {{
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            color: #FFFFFF;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .subtitle {{
            font-size: 1rem;
            font-weight: 500;
            color: #A0A0A0;
            line-height: 1.6;
            margin-bottom: 2rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .closing-message {{
            font-size: 0.875rem;
            font-weight: 500;
            color: #666666;
            margin-top: 2rem;
            letter-spacing: 0.05em;
        }}

        @media (max-width: 640px) {{
            .logo {{
                width: 150px;
                height: 150px;
                margin-bottom: 2rem;
            }}

            h1 {{
                font-size: 2rem;
            }}

            .subtitle {{
                font-size: 0.875rem;
                margin-bottom: 1.5rem;
            }}

            .closing-message {{
                font-size: 0.75rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="/deid_logo_noname.png" alt="DEiD Logo" class="logo">
        <h1>Account Already Linked</h1>
        <p class="subtitle">
            This social account is already linked to your DEiD profile.
        </p>
        <p class="closing-message">
            This window will close automatically in <span id="countdown">5</span> seconds...
        </p>
    </div>

    <script>
        // Countdown timer
        let seconds = 5;
        const countdownElement = document.getElementById('countdown');

        const interval = setInterval(() => {{
            seconds--;
            countdownElement.textContent = seconds;
            if (seconds <= 0) {{
                clearInterval(interval);
            }}
        }}, 1000);

        // Auto-close after 5 seconds
        setTimeout(() => {{
            window.close();
        }}, 5000);
    </script>
</body>
</html>
"""


def get_oauth_generic_error_template(error_message: str) -> str:
    """
    Generate HTML template for generic OAuth verification error.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Error - DEiD</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000000;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            color: #FFFFFF;
        }}

        .container {{
            width: 100%;
            max-width: 1200px;
            text-align: center;
            animation: fadeIn 0.6s ease-out;
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .logo {{
            width: 200px;
            height: 200px;
            margin: 0 auto 3rem;
            display: block;
        }}

        h1 {{
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            color: #FFFFFF;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .subtitle {{
            font-size: 1rem;
            font-weight: 500;
            color: #A0A0A0;
            line-height: 1.6;
            margin-bottom: 3rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .return-button {{
            background: linear-gradient(135deg, #EF4444, #F87171);
            color: #000000;
            border: none;
            border-radius: 3rem;
            padding: 1.25rem 3rem;
            font-size: 1.125rem;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
        }}

        .return-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(239, 68, 68, 0.5);
        }}

        .return-button:active {{
            transform: translateY(0);
        }}

        @media (max-width: 640px) {{
            .logo {{
                width: 150px;
                height: 150px;
                margin-bottom: 2rem;
            }}

            h1 {{
                font-size: 2rem;
            }}

            .subtitle {{
                font-size: 0.875rem;
                margin-bottom: 2rem;
            }}

            .return-button {{
                padding: 1rem 2.5rem;
                font-size: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="/deid_logo_noname.png" alt="DEiD Logo" class="logo">
        <h1>Verification Error</h1>
        <p class="subtitle">
            {error_message}
        </p>
        <a href="javascript:window.close()" class="return-button">
            Return to DEiD
        </a>
    </div>

    <script>
        // Auto-close after 8 seconds
        setTimeout(() => {{
            window.close();
        }}, 8000);
    </script>
</body>
</html>
"""
