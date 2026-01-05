from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def read_text(path):
    fp = os.path.join(BASE_DIR, path)
    with open(fp, 'r', encoding='utf-8') as f:
        return f.read()

def section_title(text):
    return Paragraph(text, ParagraphStyle(name='SectionTitle', fontName='Helvetica-Bold', fontSize=14, spaceBefore=12, spaceAfter=8))

def body(text):
    return Paragraph(text, ParagraphStyle(name='Body', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8))

def code(text):
    return Preformatted(text, style=ParagraphStyle(name='Code', fontName='Courier', fontSize=9, leading=12, backColor=colors.whitesmoke, leftIndent=6, rightIndent=6))

def main():
    out_dir = os.path.join(BASE_DIR, 'docs')
    os.makedirs(out_dir, exist_ok=True)
    doc = SimpleDocTemplate(os.path.join(out_dir, 'login_auth_ieee.pdf'), pagesize=LETTER, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph('User Login and Authorization in Rate My Course', ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=18, alignment=1, spaceAfter=6)))
    story.append(Paragraph('Gary Wit; Rate My Course Team', ParagraphStyle(name='Authors', fontName='Helvetica', fontSize=11, alignment=1, spaceAfter=12)))

    story.append(Paragraph('Abstract—This paper explains how the application implements user login and authorization using Django sessions and cookies. It details browser cookie behavior, server-side session and token issuance, session storage and association with users, and password verification.', styles['BodyText']))
    story.append(Paragraph('Index Terms—Authentication, Authorization, Sessions, Cookies, CSRF, Django.', styles['BodyText']))

    story.append(section_title('I. Browser Cookies and AJAX Request Authorization'))
    story.append(body('The browser stores two key cookies: sessionid (session identifier) and csrftoken (CSRF protection token). All subsequent requests automatically include sessionid. For state-changing requests, the app embeds csrftoken in forms and sets X-CSRFToken on AJAX calls.'))
    story.append(body('Login and forms include CSRF tokens, and protected AJAX endpoints read the CSRF header. Below is a real form and fetch example from the app.'))
    story.append(code(read_text('templates/login.html')))
    story.append(code('\n'.join([l for l in read_text('templates/course_detail.html').splitlines()[248:286]])))

    story.append(section_title('II. Server Identification and Cookie/Token Issuance'))
    story.append(body('Upon successful authentication, the server calls login(request, user). The session middleware persists a server-side session and returns Set-Cookie: sessionid to the browser. Authentication middleware maps session data to request.user on future requests.'))
    story.append(code('\n'.join([l for l in read_text('core/views.py').splitlines()[172:183]])))

    story.append(section_title('III. Session Storage and Association with Users'))
    story.append(body('Django stores active sessions in the django_session table. Each session record links to a session key (sessionid) and serialized session data (including the authenticated user ID). AuthenticationMiddleware reconstructs request.user from the session on each request.'))
    story.append(body('Access control uses user.is_authenticated for general checks and user.is_staff for administrative views. The app also uses @login_required to guard write operations such as rating, comments, reactions, favorites, and reports.'))
    story.append(code('\n'.join([l for l in read_text('core/views.py').splitlines()[187:206]])))

    story.append(section_title('IV. Password Verification'))
    story.append(body('Registration stores user credentials in the auth_user table using the framework’s password hashing (PBKDF2 by default). During login, authenticate() verifies the supplied password by hashing and comparing against the stored hash.'))
    story.append(code('\n'.join([l for l in read_text('core/views.py').splitlines()[152:170]])))

    story.append(section_title('V. Authentication Flow Diagram'))
    flow = '\n'.join([
        'Browser                          Server',
        '   |    GET /login                 |',
        '   |------------------------------>|',
        '   |    Render form with CSRF      |',
        '   |<------------------------------|',
        '   |    POST /login (csrf, creds)  |',
        '   |------------------------------>| authenticate -> success',
        '   |    Set-Cookie: sessionid      | login(); persist session',
        '   |<------------------------------|',
        '   |    Subsequent requests with   | read session; request.user',
        '   |    Cookie: sessionid          |',
        '   |------------------------------>|',
        '   |    POST /favorite (AJAX)      | CSRF header + session',
        '   |------------------------------>|',
        '   |    GET /logout                | logout(); expire session',
        '   |------------------------------>| Set-Cookie expires',
        '   |<------------------------------|',
    ])
    story.append(code(flow))

    story.append(section_title('VI. Security Considerations'))
    story.append(body('CSRF protection is enforced for all state-changing requests. Session cookies are HttpOnly and SameSite=Lax by default in development. For production, Secure and stricter SameSite can be enabled to reduce risk. No plaintext passwords are stored; password hashing and salting are handled by the framework.'))

    story.append(PageBreak())
    story.append(section_title('References'))
    story.append(body('[1] Django Documentation: Authentication, Sessions, CSRF'))

    doc.build(story)

if __name__ == '__main__':
    main()
