"""
HTML response templates for OAuth callbacks (DEiD).
Modern dark theme style, using Inter font and solid color palette.
"""

from typing import Optional


def get_oauth_success_template(
    platform: str,
    username: str,
    account_id: str,
    status: str,
    signature: str
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
            padding: 1rem;
            color: #FFFFFF;
        }}

        .container {{
            width: 100%;
            max-width: 32rem;
            background: #121212;
            border: 1px solid #212121;
            border-radius: 1rem;
            box-shadow: 0 25px 50px -12px rgba(75, 255, 191, 0.09);
            padding: 2.5rem;
            text-align: center;
            animation: slideUp 0.5s ease-out;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .icon-container {{
            width: 5rem;
            height: 5rem;
            background: linear-gradient(135deg, #4BFFA8, #10B981);
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            box-shadow: 0 8px 24px rgba(75, 255, 191, 0.25);
        }}

        .success-icon {{
            font-size: 2.5rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #4BFFA8, #10B981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtitle {{
            color: #A0A0A0;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 2rem;
        }}

        .user-info {{
            background: rgba(75, 255, 191, 0.08);
            border: 1px solid rgba(75, 255, 191, 0.34);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            text-align: left;
        }}

        .info-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(75, 255, 191, 0.15);
        }}

        .info-row:last-child {{
            border-bottom: none;
        }}

        .info-label {{
            font-weight: 600;
            color: #FFFFFF;
            font-size: 0.875rem;
        }}

        .info-value {{
            color: #A0A0A0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 0.875rem;
        }}

        .status-badge {{
            background: linear-gradient(135deg, #89FF89, #5EE65E);
            color: #000000;
            padding: 0.375rem 0.875rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .signature {{
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 0.8em;
            color: #78ffe1;
            word-break: break-all;
            margin-top: 1.25rem;
            padding: 0.55rem;
            background: #0d1a13;
            border: 1px solid #1ce4b4;
            border-radius: 0.5rem;
        }}

        .back-button {{
            background: linear-gradient(135deg, #4BFFA8, #10B981);
            color: #000000;
            border: none;
            border-radius: 0.75rem;
            padding: 1rem 2rem;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 1.5rem;
            box-shadow: 0 8px 24px rgba(75, 255, 191, 0.19);
        }}

        .back-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(75, 255, 191, 0.30);
        }}

        .back-button:active {{
            transform: translateY(0);
        }}

        .instruction {{
            color: #A0A0A0;
            font-size: 0.875rem;
            margin: 1.5rem 0;
            line-height: 1.6;
        }}

        @media (max-width: 640px) {{
            .container {{
                padding: 2rem 1.5rem;
                margin: 0.5rem;
            }}

            h1 {{
                font-size: 1.5rem;
            }}

            .subtitle {{
                font-size: 0.9rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon-container">
            <div class="success-icon">✅</div>
        </div>
        <h1>{platform.title()} Verification Successful!</h1>
        <p class="subtitle">
            Your {platform.title()} account has been successfully verified and linked to your DEiD profile.
        </p>

        <div class="user-info">
            <div class="info-row">
                <span class="info-label">Platform:</span>
                <span class="info-value">{platform.title()}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Username:</span>
                <span class="info-value">{username}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Account ID:</span>
                <span class="info-value">{account_id}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="status-badge">{status.title()}</span>
            </div>
            <div class="signature">
                Signature: {signature[:20]}...
            </div>
        </div>

        <p class="instruction">
            You can now close this window and return to the DEiD dApp to complete the on-chain verification.
        </p>

        <a href="javascript:window.close()" class="back-button">
            <span>Close Window & Return to DEiD</span>
        </a>
    </div>

    <script>
        // Auto-close after 10 seconds
        setTimeout(() => {{
            window.close();
        }}, 10000);
    </script>
</body>
</html>
"""


def get_oauth_error_template(
    platform: str,
    error_message: str,
    status_code: Optional[int] = None
) -> str:
    """
    Generate HTML template for OAuth verification error.
    """
    status_info = f"<br><strong>Status Code:</strong> {status_code}" if status_code else ""
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
            padding: 1rem;
            color: #FFFFFF;
        }}

        .container {{
            width: 100%;
            max-width: 32rem;
            background: #121212;
            border: 1px solid #212121;
            border-radius: 1rem;
            box-shadow: 0 25px 50px -12px rgba(239, 68, 68, 0.15);
            padding: 2.5rem;
            text-align: center;
            animation: slideUp 0.5s ease-out;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .icon-container {{
            width: 5rem;
            height: 5rem;
            background: linear-gradient(135deg, #EF4444, #F87171);
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            box-shadow: 0 8px 24px rgba(239, 68, 68, 0.27);
        }}

        .error-icon {{
            font-size: 2.5rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #EF4444, #F87171);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .error-message {{
            background: rgba(239, 68, 68, 0.09);
            border: 1px solid rgba(239, 68, 68, 0.21);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            color: #EF4444;
            font-size: 0.968rem;
            line-height: 1.6;
            text-align: left;
        }}

        .back-button {{
            background: linear-gradient(135deg, #EF4444, #F87171);
            color: #FFF;
            border: none;
            border-radius: 0.75rem;
            padding: 1rem 2rem;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 1.5rem;
            box-shadow: 0 8px 24px rgba(239, 68, 68, 0.26);
        }}

        .back-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(239, 68, 68, 0.39);
        }}

        .back-button:active {{
            transform: translateY(0);
        }}

        .instruction {{
            color: #A0A0A0;
            font-size: 0.875rem;
            margin: 1.5rem 0;
            line-height: 1.6;
        }}

        @media (max-width: 640px) {{
            .container {{
                padding: 2rem 1.5rem;
                margin: 0.5rem;
            }}

            h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon-container">
            <div class="error-icon">❌</div>
        </div>
        <h1>{platform.title()} Verification Failed</h1>
        <div class="error-message">
            <strong>Error:</strong> {error_message}{status_info}
        </div>
        <p class="instruction">
            Please try again or contact support if the problem persists.
        </p>
        <a href="javascript:window.close()" class="back-button">
            <span>Close Window & Return to DEiD</span>
        </a>
    </div>
</body>
</html>
"""


def get_oauth_already_linked_template(
    platform: str,
    username: str,
    account_id: str,
    status: str
) -> str:
    """
    Generate HTML template for already linked OAuth account.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{platform.title()} Account Already Linked - DEiD</title>
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
            padding: 1rem;
            color: #FFFFFF;
        }}

        .container {{
            width: 100%;
            max-width: 32rem;
            background: #121212;
            border: 1px solid #212121;
            border-radius: 1rem;
            box-shadow: 0 25px 50px -12px rgba(255, 168, 75, 0.15);
            padding: 2.5rem;
            text-align: center;
            animation: slideUp 0.5s ease-out;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .icon-container {{
            width: 5rem;
            height: 5rem;
            background: linear-gradient(135deg, #FFA84B, #F59E0B);
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            box-shadow: 0 8px 24px rgba(255, 168, 75, 0.3);
        }}

        .info-icon {{
            font-size: 2.5rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #FFA84B, #F59E0B);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtitle {{
            color: #A0A0A0;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 2rem;
        }}

        .user-info {{
            background: rgba(255, 168, 75, 0.1);
            border: 1px solid rgba(255, 168, 75, 0.3);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            text-align: left;
        }}

        .info-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(255, 168, 75, 0.2);
        }}

        .info-row:last-child {{
            border-bottom: none;
        }}

        .info-label {{
            font-weight: 600;
            color: #FFFFFF;
            font-size: 0.875rem;
        }}

        .info-value {{
            color: #A0A0A0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 0.875rem;
        }}

        .status-badge {{
            background: linear-gradient(135deg, #89FF89, #5EE65E);
            color: #000000;
            padding: 0.375rem 0.875rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .back-button {{
            background: linear-gradient(135deg, #FFA84B, #F59E0B);
            color: white;
            border: none;
            border-radius: 0.75rem;
            padding: 1rem 2rem;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 1.5rem;
            box-shadow: 0 8px 24px rgba(255, 168, 75, 0.3);
        }}

        .back-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(255, 168, 75, 0.4);
        }}

        .back-button:active {{
            transform: translateY(0);
        }}

        .instruction {{
            color: #A0A0A0;
            font-size: 0.875rem;
            margin: 1.5rem 0;
            line-height: 1.6;
        }}

        @media (max-width: 640px) {{
            .container {{
                padding: 2rem 1.5rem;
                margin: 0.5rem;
            }}

            h1 {{
                font-size: 1.5rem;
            }}

            .subtitle {{
                font-size: 0.9rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon-container">
            <div class="info-icon">ℹ️</div>
        </div>
        <h1>Account Already Linked!</h1>
        <p class="subtitle">
            This {platform.title()} account is already linked to your DEiD profile.
        </p>

        <div class="user-info">
            <div class="info-row">
                <span class="info-label">Platform:</span>
                <span class="info-value">{platform.title()}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Username:</span>
                <span class="info-value">{username}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Account ID:</span>
                <span class="info-value">{account_id}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="status-badge">{status.title()}</span>
            </div>
        </div>

        <p class="instruction">
            No action needed. You can close this window and return to the DEiD dApp.
        </p>

        <a href="javascript:window.close()" class="back-button">
            <span>Close Window & Return to DEiD</span>
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


def get_oauth_generic_error_template(
    error_message: str
) -> str:
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
            padding: 1rem;
            color: #FFFFFF;
        }}

        .container {{
            width: 100%;
            max-width: 32rem;
            background: #121212;
            border: 1px solid #212121;
            border-radius: 1rem;
            box-shadow: 0 25px 50px -12px rgba(255, 168, 75, 0.12);
            padding: 2.5rem;
            text-align: center;
            animation: slideUp 0.5s ease-out;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .icon-container {{
            width: 5rem;
            height: 5rem;
            background: linear-gradient(135deg, #FFA84B, #F59E0B);
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            box-shadow: 0 8px 24px rgba(255, 168, 75, 0.22);
        }}

        .error-icon {{
            font-size: 2.5rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #FFA84B, #F59E0B);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .error-message {{
            background: rgba(255, 168, 75, 0.07);
            border: 1px solid rgba(255, 168, 75, 0.2);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            color: #FFA84B;
            font-size: 0.968rem;
            line-height: 1.6;
            text-align: left;
        }}

        .back-button {{
            background: linear-gradient(135deg, #FFA84B, #F59E0B);
            color: #000;
            border: none;
            border-radius: 0.75rem;
            padding: 1rem 2rem;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 1.5rem;
            box-shadow: 0 8px 24px rgba(255, 168, 75, 0.29);
        }}

        .back-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(255, 168, 75, 0.41);
        }}

        .back-button:active {{
            transform: translateY(0);
        }}

        .instruction {{
            color: #A0A0A0;
            font-size: 0.875rem;
            margin: 1.5rem 0;
            line-height: 1.6;
        }}

        @media (max-width: 640px) {{
            .container {{
                padding: 2rem 1.5rem;
                margin: 0.5rem;
            }}

            h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon-container">
            <div class="error-icon">⚠️</div>
        </div>
        <h1>Verification Error</h1>
        <div class="error-message">
            <strong>Internal Server Error:</strong><br>
            {error_message}
        </div>
        <p class="instruction">
            Please try again or contact support if the problem persists.
        </p>
        <a href="javascript:window.close()" class="back-button">
            <span>Close Window & Return to DEiD</span>
        </a>
    </div>
</body>
</html>
"""
