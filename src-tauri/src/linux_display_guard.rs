//! Linux Display Guard: Intercepts fatal display disconnections (both X11 and Wayland)
//! and transitions the application to headless background mode rather than crashing
//! the core port 8045 proxy service.

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};

/// Global flag set when display connection is lost (Wayland broken pipe or X11 IO error).
static DISPLAY_DISCONNECTED: AtomicBool = AtomicBool::new(false);

/// Flag indicating user or application logic explicitly requested a full process termination
/// (e.g. CLI subcommands, tray menu "Exit", web UI exit command, or SIGTERM/SIGINT signal).
static USER_INITIATED_EXIT: AtomicBool = AtomicBool::new(false);

/// GUI main thread ID (POSIX pthread_t)
#[cfg_attr(not(target_os = "linux"), allow(dead_code))]
static MAIN_THREAD_ID: AtomicU64 = AtomicU64::new(0);

/// Check if display connection was lost
pub fn is_display_disconnected() -> bool {
    DISPLAY_DISCONNECTED.load(Ordering::SeqCst)
}

/// Set display disconnected state
pub fn set_display_disconnected(val: bool) {
    DISPLAY_DISCONNECTED.store(val, Ordering::SeqCst);
}

/// Mark that the user or intentional system signal requested a complete exit
pub fn mark_user_initiated_exit() {
    USER_INITIATED_EXIT.store(true, Ordering::SeqCst);
}

/// Check if the exit was intentionally initiated by user or signal
pub fn is_user_initiated_exit() -> bool {
    USER_INITIATED_EXIT.load(Ordering::SeqCst)
}

/// Record the thread ID of the main GUI thread
#[cfg(target_os = "linux")]
pub fn record_main_thread_id() {
    let tid = unsafe { libc::pthread_self() };
    MAIN_THREAD_ID.store(tid as u64, Ordering::SeqCst);
}

#[cfg(not(target_os = "linux"))]
pub fn record_main_thread_id() {}

/// Matcher for display disconnection messages from GDK, GTK, Xlib, or Wayland.
/// Pure function testable on any platform without GTK/X11 dependencies.
pub fn is_display_disconnect_message(domain: &str, msg: &str) -> bool {
    let lower = msg.to_lowercase();
    let is_gdk_or_gtk = domain.is_empty()
        || domain.eq_ignore_ascii_case("gdk")
        || domain.eq_ignore_ascii_case("gtk")
        || domain.eq_ignore_ascii_case("glib");

    // 1. Wayland connection loss patterns
    if lower.contains("lost connection to wayland")
        || (lower.contains("broken pipe") && lower.contains("wayland"))
        || lower.contains("dispatching to wayland display")
    {
        return true;
    }

    // 2. X11 / xrdp / VNC connection loss patterns
    // e.g.:
    // "Fatal IO error 11 (Resource temporarily unavailable) on X server :10."
    // "Fatal IO error 32 (Broken pipe) on X server :10."
    // "Fatal IO error 104 (Connection reset by peer) on X server :10."
    // "The application 'antigravity-tools' lost its connection to the display :10"
    // "X connection to :10 broken (explicit kill or server shutdown)"
    if lower.contains("fatal io error")
        || lower.contains("on x server")
        || lower.contains("x connection to")
        || lower.contains("lost its connection to the display")
        || lower.contains("error reading events from display")
        || lower.contains("error flushing display")
    {
        return true;
    }

    // 3. Display-related generic broken connection patterns
    if (is_gdk_or_gtk || lower.contains("display") || lower.contains("server"))
        && (lower.contains("broken pipe")
            || lower.contains("断开的管道")
            || lower.contains("connection reset by peer")
            || lower.contains("连接被对方重置")
            || lower.contains("protocol error")
            || lower.contains("resource temporarily unavailable"))
    {
        return true;
    }

    false
}

#[cfg(target_os = "linux")]
type GLogLevelFlags = i32;
#[cfg(target_os = "linux")]
type GLogFunc = Option<
    unsafe extern "C" fn(
        log_domain: *const std::os::raw::c_char,
        log_level: GLogLevelFlags,
        message: *const std::os::raw::c_char,
        user_data: *mut std::os::raw::c_void,
    ),
>;

#[cfg(target_os = "linux")]
static PREVIOUS_GLOG_HANDLER: std::sync::atomic::AtomicPtr<()> =
    std::sync::atomic::AtomicPtr::new(std::ptr::null_mut());

#[cfg(target_os = "linux")]
extern "C" {
    fn g_log_set_default_handler(
        log_func: GLogFunc,
        user_data: *mut std::os::raw::c_void,
    ) -> GLogFunc;
}

#[cfg(target_os = "linux")]
unsafe extern "C" fn custom_gdk_log_handler(
    log_domain: *const std::os::raw::c_char,
    log_level: GLogLevelFlags,
    message: *const std::os::raw::c_char,
    user_data: *mut std::os::raw::c_void,
) {
    if !message.is_null() {
        let msg_cstr = std::ffi::CStr::from_ptr(message);
        let msg_str = msg_cstr.to_string_lossy();
        let domain_str = if !log_domain.is_null() {
            std::ffi::CStr::from_ptr(log_domain).to_string_lossy()
        } else {
            std::borrow::Cow::Borrowed("")
        };

        if is_display_disconnect_message(&domain_str, &msg_str) {
            eprintln!(
                "\x1b[33m[Antigravity Manager]\x1b[0m Caught display disconnect log: {}",
                msg_str
            );
            set_display_disconnected(true);
        }
    }

    let prev_ptr = PREVIOUS_GLOG_HANDLER.load(Ordering::SeqCst);
    if !prev_ptr.is_null() {
        let prev_fn: unsafe extern "C" fn(
            *const std::os::raw::c_char,
            GLogLevelFlags,
            *const std::os::raw::c_char,
            *mut std::os::raw::c_void,
        ) = std::mem::transmute(prev_ptr);
        prev_fn(log_domain, log_level, message, user_data);
    } else {
        libc::printf(b"%s\n\0".as_ptr() as *const _, message);
    }
}

#[cfg(target_os = "linux")]
type XIOErrorHandler = unsafe extern "C" fn(*mut std::ffi::c_void) -> std::os::raw::c_int;

#[cfg(target_os = "linux")]
static PREVIOUS_XIO_HANDLER: std::sync::atomic::AtomicPtr<()> =
    std::sync::atomic::AtomicPtr::new(std::ptr::null_mut());

#[cfg(target_os = "linux")]
unsafe extern "C" fn custom_x_io_error_handler(
    display: *mut std::ffi::c_void,
) -> std::os::raw::c_int {
    eprintln!(
        "\x1b[33m[Antigravity Manager]\x1b[0m Caught fatal X11 IO error (remote desktop / X server disconnected). \
         Main GUI thread transitioning to headless fallback mode; port 8045 proxy service remains ACTIVE."
    );
    set_display_disconnected(true);

    // Call previous handler if it exists
    let prev_ptr = PREVIOUS_XIO_HANDLER.load(Ordering::SeqCst);
    if !prev_ptr.is_null() {
        let prev_fn: unsafe extern "C" fn(*mut std::ffi::c_void) -> std::os::raw::c_int =
            std::mem::transmute(prev_ptr);
        let _ = prev_fn(display);
    }

    // Safely terminate only the crashing GUI thread, allowing Tokio runtime and port 8045 to continue
    libc::pthread_exit(std::ptr::null_mut());
}

#[cfg(target_os = "linux")]
fn init_x11_io_guard() {
    unsafe {
        // Try loading libX11.so.6 dynamically without adding a rigid compile-time linkage dependency
        let lib = libc::dlopen(
            b"libX11.so.6\0".as_ptr() as *const _,
            libc::RTLD_LAZY | libc::RTLD_NOLOAD,
        );
        let lib = if lib.is_null() {
            libc::dlopen(b"libX11.so.6\0".as_ptr() as *const _, libc::RTLD_LAZY)
        } else {
            lib
        };

        if !lib.is_null() {
            let fn_sym = libc::dlsym(lib, b"XSetIOErrorHandler\0".as_ptr() as *const _);
            if !fn_sym.is_null() {
                let set_io_handler: unsafe extern "C" fn(
                    Option<XIOErrorHandler>,
                )
                    -> Option<XIOErrorHandler> = std::mem::transmute(fn_sym);
                let old = set_io_handler(Some(custom_x_io_error_handler));
                if let Some(old_fn) = old {
                    PREVIOUS_XIO_HANDLER.store(old_fn as *mut (), Ordering::SeqCst);
                }
                tracing::info!(
                    "[Linux Display Guard] X11 native XSetIOErrorHandler hooked successfully."
                );
            }
        }
    }
}

/// Initialize the Linux GDK and X11 display disconnection guards.
#[cfg(target_os = "linux")]
pub fn init_display_guard() {
    unsafe {
        let old = g_log_set_default_handler(Some(custom_gdk_log_handler), std::ptr::null_mut());
        if let Some(old_fn) = old {
            PREVIOUS_GLOG_HANDLER.store(old_fn as *mut (), Ordering::SeqCst);
        }
    }
    init_x11_io_guard();
    tracing::info!(
        "[Linux Display Guard] Universal X11/Wayland display disconnect guard initialized."
    );
}

#[cfg(not(target_os = "linux"))]
pub fn init_display_guard() {}

/// Intercept `_exit` on Linux so display loss or worker crash does not kill Tokio runtime and port 8045.
#[cfg(target_os = "linux")]
#[no_mangle]
pub unsafe extern "C" fn _exit(status: std::os::raw::c_int) -> ! {
    // 1. If this exit was deliberately triggered by user/signal, terminate cleanly.
    if is_user_initiated_exit() {
        libc::syscall(libc::SYS_exit_group, status);
        loop {}
    }

    // 2. [Fix #3757] Any other _exit call from C/GTK/WebKit/Xlib/IPC is UNEXPECTED.
    // Whether it was called from the GUI main thread (display drop) or a background worker
    // thread (e.g. WebKit IPC worker, GTK helper, or Tokio worker during account refresh),
    // we must strictly prevent SYS_exit_group from destroying the process group and killing
    // the core port 8045 proxy service!
    let current_tid = libc::pthread_self() as u64;
    let main_tid = MAIN_THREAD_ID.load(Ordering::SeqCst);
    let is_main_thread = main_tid != 0 && current_tid == main_tid;

    set_display_disconnected(true);

    if is_main_thread {
        eprintln!(
            "\x1b[32m[Antigravity Manager]\x1b[0m Linux GUI main thread caught fatal exit (status {}). \
             Main GUI thread terminating cleanly; Tokio runtime and port 8045 proxy service remain ACTIVE in headless fallback.",
            status
        );
    } else {
        eprintln!(
            "\x1b[33m[Antigravity Manager]\x1b[0m Linux worker thread 0x{:x} caught unhandled _exit({}) (display/IPC/GTK drop). \
             Isolating and terminating failing thread only; core port 8045 proxy service remains ACTIVE.",
            current_tid, status
        );
    }

    libc::pthread_exit(std::ptr::null_mut());
}

/// Intercept `_Exit` on Linux as well.
#[cfg(target_os = "linux")]
#[no_mangle]
pub unsafe extern "C" fn _Exit(status: std::os::raw::c_int) -> ! {
    _exit(status);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_display_disconnect_message_recognition() {
        // Wayland disconnection patterns
        assert!(is_display_disconnect_message(
            "Gdk",
            "Error reading events from display: Broken pipe"
        ));
        assert!(is_display_disconnect_message(
            "Gdk",
            "Error reading events from display: 断开的管道"
        ));
        assert!(is_display_disconnect_message(
            "Gdk",
            "Error reading events from display: 连接被对方重置"
        ));
        assert!(is_display_disconnect_message(
            "",
            "Lost connection to Wayland compositor"
        ));
        assert!(is_display_disconnect_message(
            "Gtk",
            "Error 32 (Broken pipe) dispatching to Wayland display"
        ));

        // X11 / xrdp disconnection patterns (Issue #3752)
        assert!(is_display_disconnect_message(
            "Gdk",
            "The application 'antigravity-tools' lost its connection to the display :0"
        ));
        assert!(is_display_disconnect_message(
            "Gdk",
            "The application 'antigravity-tools' lost its connection to the display :10.0"
        ));
        assert!(is_display_disconnect_message(
            "Gdk",
            "antigravity-tools: Fatal IO error 11 (Resource temporarily unavailable) on X server :10."
        ));
        assert!(is_display_disconnect_message(
            "Gdk",
            "antigravity-tools: Fatal IO error 32 (Broken pipe) on X server :10."
        ));
        assert!(is_display_disconnect_message(
            "Gdk",
            "antigravity-tools: Fatal IO error 104 (Connection reset by peer) on X server :10."
        ));
        assert!(is_display_disconnect_message(
            "",
            "X connection to :10 broken (explicit kill or server shutdown)"
        ));
        assert!(is_display_disconnect_message(
            "GLib",
            "Error flushing display: Protocol error"
        ));

        // Normal logs must NOT trigger display disconnect
        assert!(!is_display_disconnect_message("Gdk", "Normal gdk warning"));
        assert!(!is_display_disconnect_message(
            "App",
            "Proxy request failed: connection reset"
        ));
        assert!(!is_display_disconnect_message(
            "",
            "Some unrelated log message"
        ));
    }

    #[test]
    fn test_display_disconnect_flag() {
        set_display_disconnected(false);
        assert!(!is_display_disconnected());
        set_display_disconnected(true);
        assert!(is_display_disconnected());
        set_display_disconnected(false);
    }

    #[test]
    fn test_user_initiated_exit_flag() {
        mark_user_initiated_exit();
        assert!(is_user_initiated_exit());
    }
}
