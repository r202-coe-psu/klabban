from flask import Flask, render_template


def init_error_handling(app: Flask):
    @app.errorhandler(401)
    def unauthorized(e):
        return (
            render_template(
                "base/error.html",
                error_msg="Unauthorized: You must be logged in to access this page.",
            ),
            401,
        )

    @app.errorhandler(403)
    def forbidden(e):
        return (
            render_template(
                "base/error.html",
                error_msg="Access Denied: You do not have permission to access this page.",
            ),
            403,
        )

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("base/error.html", error_msg="Page Not Found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return (
            render_template(
                "base/error.html",
                # error_msg="An error occurred. Please try again later.",
                error_msg="กำลังอัปเดตระบบ กรุณารอสักครู่...",
                error_msg_eng="Please wait a moment, the system is updating...",
            ),
            500,
        )
