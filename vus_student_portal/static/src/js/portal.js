/**
 * VUS Student Portal - Client-side SPA Application Logic
 */
(function() {
    function initPortal() {
        console.log("VUS Student Portal JS Initializing...");

        // Current application state
        let state = {
            student: null,
            courses: [],
            classes: [],
            invoices: [],
            attendance: [],
            my_classes: [],
            activeTab: 'overview'
        };

        // DOM Elements
        const loginScreen = document.getElementById('login-screen');
        const portalScreen = document.getElementById('portal-screen');
        const loginForm = document.getElementById('login-form');
        const consultForm = document.getElementById('consult-form');
        const btnLogout = document.getElementById('btn-logout');
        const toastContainer = document.getElementById('toast-container');
        const navItems = document.querySelectorAll('.nav-item');
        const tabContents = document.querySelectorAll('.tab-content');
        const consultCourseSelect = document.getElementById('consult_course');
        const goToConsultLink = document.getElementById('go-to-consult');

        // Check if vital elements are present
        if (!loginScreen || !portalScreen || !loginForm) {
            console.error("Critical elements not found in the DOM!");
            showToast("Lỗi tải trang: Không tìm thấy các phần tử giao diện quan trọng. Vui lòng làm mới trang (F5).", "error");
            return;
        }

        // Check session status
        checkSession();

        // Attach event listeners
        loginForm.addEventListener('submit', handleLogin);
        if (consultForm) consultForm.addEventListener('submit', handleConsultSubmit);
        if (btnLogout) btnLogout.addEventListener('click', handleLogout);
        
        // Navigation clicks
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const tabName = item.getAttribute('data-tab');
                switchTab(tabName);
            });
        });

        // "Go to consult" link on login page
        if (goToConsultLink) {
            goToConsultLink.addEventListener('click', (e) => {
                e.preventDefault();
                loginScreen.style.display = 'none';
                portalScreen.style.display = 'flex';
                // Hide header navigation items that require login
                document.querySelectorAll('.nav-menu button:not([data-tab="consult"])').forEach(btn => {
                    btn.style.display = 'none';
                });
                document.querySelector('.user-control').style.display = 'none';
                switchTab('consult');
            });
        }

        // --- Toast Notification System ---
        function showToast(message, type = 'success') {
            if (!toastContainer) {
                console.log(`[Toast ${type}]: ${message}`);
                return;
            }
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            let icon = 'fa-check-circle text-success';
            if (type === 'error') icon = 'fa-exclamation-circle text-danger';
            if (type === 'warning') icon = 'fa-exclamation-triangle text-warning';
            if (type === 'info') icon = 'fa-info-circle text-info';

            toast.innerHTML = `
                <i class="fa ${icon}"></i>
                <span>${message}</span>
            `;
            
            toastContainer.appendChild(toast);

            // Remove toast after 4 seconds
            setTimeout(() => {
                toast.style.animation = 'fadeOut 0.5s ease forwards';
                setTimeout(() => {
                    toast.remove();
                }, 500);
            }, 4000);
        }
        window.showToast = showToast;

        // --- Custom Modern Confirm Modal Dialog ---
        function showConfirmModal({ title = 'Xác nhận', message = '', icon = 'fa-exclamation-triangle', iconBg = '#FEF3C7', iconColor = '#D97706', confirmText = 'Xác nhận', cancelText = 'Hủy bỏ', confirmBtnClass = 'btn-secondary', onConfirm }) {
            let modal = document.getElementById('custom-confirm-modal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'custom-confirm-modal';
                modal.style.cssText = 'display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(12,43,92,0.45); backdrop-filter:blur(6px); z-index:99999; justify-content:center; align-items:center; animation:fadeIn 0.2s ease;';
                modal.innerHTML = `
                    <div style="background:#FFFFFF; border-radius:16px; max-width:440px; width:90%; padding:28px 24px; box-shadow:0 20px 60px rgba(12,43,92,0.25); text-align:center; border:1px solid #E2E8F0; transform:scale(0.95); transition:transform 0.2s ease;">
                        <div id="confirm-modal-icon-wrapper" style="width:56px; height:56px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:24px; margin:0 auto 16px;">
                            <i id="confirm-modal-icon" class="fa"></i>
                        </div>
                        <h3 id="confirm-modal-title" style="color:#0C2B5C; font-size:18px; font-weight:700; margin-bottom:8px;"></h3>
                        <p id="confirm-modal-message" style="color:#475569; font-size:14px; line-height:1.5; margin-bottom:24px;"></p>
                        <div style="display:flex; gap:12px; justify-content:center;">
                            <button id="btn-confirm-cancel" class="btn btn-outline" style="flex:1; padding:10px; border-radius:8px; font-size:14px;"></button>
                            <button id="btn-confirm-ok" class="btn" style="flex:1; padding:10px; border-radius:8px; font-size:14px; font-weight:700;"></button>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }

            const iconWrapper = modal.querySelector('#confirm-modal-icon-wrapper');
            const iconEl = modal.querySelector('#confirm-modal-icon');
            const titleEl = modal.querySelector('#confirm-modal-title');
            const msgEl = modal.querySelector('#confirm-modal-message');
            const okBtn = modal.querySelector('#btn-confirm-ok');
            const cancelBtn = modal.querySelector('#btn-confirm-cancel');

            iconWrapper.style.backgroundColor = iconBg;
            iconWrapper.style.color = iconColor;
            iconEl.className = `fa ${icon}`;
            titleEl.textContent = title;
            msgEl.textContent = message;
            okBtn.textContent = confirmText;
            okBtn.className = `btn ${confirmBtnClass}`;
            cancelBtn.textContent = cancelText;

            modal.style.display = 'flex';

            const cleanup = () => {
                modal.style.display = 'none';
                okBtn.onclick = null;
                cancelBtn.onclick = null;
            };

            cancelBtn.onclick = () => {
                cleanup();
            };

            okBtn.onclick = () => {
                cleanup();
                if (onConfirm) onConfirm();
            };
        }

        // --- Formatters ---
        function formatCurrency(value) {
            return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
        }

        function formatDate(dateStr) {
            if (!dateStr) return '';
            const parts = dateStr.split('-');
            if (parts.length !== 3) return dateStr;
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }

        // --- SPA Session & Login Management ---
        async function checkSession() {
            try {
                console.log("Checking active session...");
                const res = await fetch('/student/api/info');
                const data = await res.json();
                if (data.status === 'success') {
                    console.log("Active session found for student:", data.student.name);
                    state.student = data.student;
                    showPortalDashboard();
                } else {
                    console.log("No active session found.");
                    showLoginScreen();
                }
            } catch (err) {
                console.error("Session check failed:", err);
                showLoginScreen();
            }
        }

        async function handleLogin(e) {
            e.preventDefault();
            console.log("Submitting login form...");
            const codeInput = document.getElementById('student_code');
            const dobInput = document.getElementById('dob');

            const student_code = codeInput.value.trim();
            const dob = dobInput.value;

            if (!student_code || !dob) {
                showToast('Vui lòng nhập đầy đủ thông tin!', 'warning');
                return;
            }

            try {
                const res = await fetch('/student/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ student_code, dob })
                });
                const data = await res.json();

                if (data.status === 'success') {
                    state.student = data.student;
                    showToast(`Chào mừng ${data.student.name} quay trở lại!`, 'success');
                    
                    // Reset form inputs
                    codeInput.value = '';
                    dobInput.value = '';
                    
                    // Show header navigation items again (if they were hidden during consult guest view)
                    document.querySelectorAll('.nav-menu button').forEach(btn => {
                        btn.style.display = 'flex';
                    });
                    const userCtrl = document.querySelector('.user-control');
                    if (userCtrl) userCtrl.style.display = 'flex';
                    
                    showPortalDashboard();
                } else {
                    showToast(data.message || 'Đăng nhập không thành công!', 'error');
                }
            } catch (err) {
                console.error("Login request failed:", err);
                showToast('Lỗi kết nối máy chủ Odoo, vui lòng thử lại sau!', 'error');
            }
        }

        async function handleLogout() {
            try {
                const res = await fetch('/student/api/logout', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success') {
                    state.student = null;
                    showToast('Đã đăng xuất tài khoản.', 'info');
                    showLoginScreen();
                }
            } catch (err) {
                console.error("Logout failed:", err);
            }
        }

        function showLoginScreen() {
            portalScreen.style.display = 'none';
            loginScreen.style.display = 'flex';
        }

        function showPortalDashboard() {
            loginScreen.style.display = 'none';
            portalScreen.style.display = 'flex';

            // Render header user details
            const headerName = document.getElementById('header-student-name');
            const headerCode = document.getElementById('header-student-code');
            if (headerName) headerName.textContent = state.student.name;
            if (headerCode) headerCode.textContent = state.student.student_code;

            // Switch to default overview tab
            switchTab('overview');
        }

        // --- Tab / SPA Navigation ---
        function switchTab(tabName) {
            state.activeTab = tabName;
            console.log("Switching to tab:", tabName);
            
            // Update nav buttons class
            navItems.forEach(item => {
                if (item.getAttribute('data-tab') === tabName) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });

            // Show/hide sections
            tabContents.forEach(content => {
                if (content.id === `tab-${tabName}`) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });

            // Trigger dynamic tab load
            loadTabData(tabName);
        }

        function loadTabData(tabName) {
            if (tabName === 'overview') {
                loadOverviewData();
            } else if (tabName === 'my-classes') {
                loadMyClassesData();
            } else if (tabName === 'classes') {
                loadClassesData();
            } else if (tabName === 'tuition') {
                loadTuitionData();
            } else if (tabName === 'attendance') {
                loadAttendanceData();
            } else if (tabName === 'consult') {
                loadConsultationData();
            }
        }

        // --- Fetch & Render Tab Contents ---

        // 1. Overview Tab
        async function loadOverviewData() {
            if (!state.student) return;

            // Update basic info labels
            const welcomeName = document.getElementById('overview-welcome-name');
            const codeEl = document.getElementById('overview-student-code');
            const nameEl = document.getElementById('overview-student-name');
            const dobEl = document.getElementById('overview-student-dob');
            const phoneEl = document.getElementById('overview-student-phone');
            const emailEl = document.getElementById('overview-student-email');
            const statusEl = document.getElementById('overview-student-status-text');
            const badgeEl = document.getElementById('overview-student-status');

            if (welcomeName) welcomeName.textContent = state.student.name;
            if (codeEl) codeEl.textContent = state.student.student_code;
            if (nameEl) nameEl.textContent = state.student.name;
            if (dobEl) dobEl.textContent = formatDate(state.student.dob);
            if (phoneEl) phoneEl.textContent = state.student.phone || 'Chưa cung cấp';
            if (emailEl) emailEl.textContent = state.student.email || 'Chưa cung cấp';
            if (statusEl) statusEl.textContent = state.student.status;
            if (badgeEl) {
                badgeEl.textContent = state.student.status;
            }

            // Fetch tuition & attendance to update summary cards
            try {
                // Load Invoices
                const resInvoices = await fetch('/student/api/invoices');
                const dataInvoices = await resInvoices.json();
                let unpaidAmount = 0;
                if (dataInvoices.status === 'success') {
                    dataInvoices.invoices.forEach(inv => {
                        if (inv.payment_state === 'Chờ thanh toán' || inv.payment_state === 'Nháp' || inv.state === 'draft' || inv.state === 'confirmed') {
                            unpaidAmount += inv.amount;
                        }
                    });
                    const unpaidEl = document.getElementById('overview-unpaid-invoices');
                    if (unpaidEl) unpaidEl.textContent = formatCurrency(unpaidAmount);
                }

                // Load Attendance rate
                const resAtt = await fetch('/student/api/attendance');
                const dataAtt = await resAtt.json();
                const rateEl = document.getElementById('overview-attendance-rate');
                if (rateEl) {
                    if (dataAtt.status === 'success' && dataAtt.attendance.length > 0) {
                        const total = dataAtt.attendance.length;
                        const presents = dataAtt.attendance.filter(a => a.status === 'present' || a.status === 'late').length;
                        const rate = Math.round((presents / total) * 100);
                        rateEl.textContent = `${rate}%`;
                    } else {
                        rateEl.textContent = `100%`;
                    }
                }
                // Load Schedule Calendar
                loadStudentScheduleCalendar();
            } catch (err) {
                console.error("Error loading overview summary data:", err);
            }
        }

        let calendarDateState = new Date();
        let cachedScheduleEvents = [];

        async function loadStudentScheduleCalendar() {
            const calendarContainer = document.getElementById('student-schedule-calendar-container');
            if (!calendarContainer) return;

            try {
                const res = await fetch('/student/api/schedule');
                const data = await res.json();
                if (data.status !== 'success' || !data.schedule_events || data.schedule_events.length === 0) {
                    calendarContainer.innerHTML = `<div class="text-center py-4 text-muted"><i class="fa fa-info-circle"></i> Chưa có dữ liệu lịch học.</div>`;
                    return;
                }

                cachedScheduleEvents = data.schedule_events;

                // Default to month of first upcoming event or active sessions
                if (cachedScheduleEvents.length > 0) {
                    const todayStr = new Date().toISOString().split('T')[0];
                    const upcomingEv = cachedScheduleEvents.find(e => e.date >= todayStr);
                    if (upcomingEv) {
                        const parts = upcomingEv.date.split('-');
                        calendarDateState = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, 1);
                    } else {
                        const parts = cachedScheduleEvents[0].date.split('-');
                        calendarDateState = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, 1);
                    }
                }

                renderScheduleCalendar();
            } catch (err) {
                console.error("Failed to load schedule calendar:", err);
                calendarContainer.innerHTML = `<div class="text-center py-4 text-danger">Không thể tải lịch học.</div>`;
            }
        }

        function renderScheduleCalendar() {
            const calendarContainer = document.getElementById('student-schedule-calendar-container');
            if (!calendarContainer || cachedScheduleEvents.length === 0) return;

            const eventsByDate = {};
            cachedScheduleEvents.forEach(ev => {
                if (!eventsByDate[ev.date]) eventsByDate[ev.date] = [];
                eventsByDate[ev.date].push(ev);
            });

            const year = calendarDateState.getFullYear();
            const month = calendarDateState.getMonth(); // 0-indexed

            const firstDayOfMonth = new Date(year, month, 1);
            const lastDayOfMonth = new Date(year, month + 1, 0);

            let startDow = firstDayOfMonth.getDay() - 1; // 0 = Mon, 6 = Sun
            if (startDow < 0) startDow = 6;

            const todayObj = new Date();
            const todayStr = todayObj.toISOString().split('T')[0];

            let html = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <button id="cal-prev-month" class="btn btn-sm btn-outline-secondary" style="padding:3px 10px; font-size:12px;" title="Tháng trước"><i class="fa fa-chevron-left"></i></button>
                        <h4 style="font-size:15px; font-weight:700; color:#0C2B5C; margin:0;">Tháng ${month + 1}/${year}</h4>
                        <button id="cal-next-month" class="btn btn-sm btn-outline-secondary" style="padding:3px 10px; font-size:12px;" title="Tháng sau"><i class="fa fa-chevron-right"></i></button>
                        <button id="cal-today-btn" class="btn btn-sm btn-light" style="padding:3px 10px; font-size:12px; border:1px solid #CBD5E1;">Hôm nay</button>
                    </div>
                    <span class="badge badge-info" style="font-size:12px; padding:6px 12px;">Tổng ${cachedScheduleEvents.length} buổi học</span>
                </div>

                <div class="calendar-grid">
                    <div class="calendar-dow-header">Thứ 2</div>
                    <div class="calendar-dow-header">Thứ 3</div>
                    <div class="calendar-dow-header">Thứ 4</div>
                    <div class="calendar-dow-header">Thứ 5</div>
                    <div class="calendar-dow-header">Thứ 6</div>
                    <div class="calendar-dow-header">Thứ 7</div>
                    <div class="calendar-dow-header">Chủ nhật</div>
            `;

            const prevMonthLastDay = new Date(year, month, 0).getDate();
            for (let i = startDow - 1; i >= 0; i--) {
                const dNum = prevMonthLastDay - i;
                html += `<div class="calendar-day-cell other-month"><span class="day-number">${dNum}</span></div>`;
            }

            for (let day = 1; day <= lastDayOfMonth.getDate(); day++) {
                const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                const isToday = (dateStr === todayStr);
                const dayEvents = eventsByDate[dateStr] || [];

                html += `
                    <div class="calendar-day-cell ${isToday ? 'is-today' : ''}">
                        <span class="day-number">${day}</span>
                        ${dayEvents.map(ev => `
                            <div class="schedule-chip" data-class-id="${ev.class_id}" data-ev-id="${ev.id}" style="background:${ev.color}; cursor:pointer;" title="Nhấp để xem chi tiết &amp; điểm danh: ${ev.title} - ${ev.session}">
                                <i class="fa fa-info-circle" style="font-size:9px;"></i> ${ev.title.length > 10 ? ev.title.substring(0, 9) + '..' : ev.title}
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            html += `</div>`;
            calendarContainer.innerHTML = html;

            // Bind month navigation clicks
            const btnPrev = document.getElementById('cal-prev-month');
            const btnNext = document.getElementById('cal-next-month');
            const btnToday = document.getElementById('cal-today-btn');

            if (btnPrev) {
                btnPrev.addEventListener('click', () => {
                    calendarDateState.setMonth(calendarDateState.getMonth() - 1);
                    renderScheduleCalendar();
                });
            }
            if (btnNext) {
                btnNext.addEventListener('click', () => {
                    calendarDateState.setMonth(calendarDateState.getMonth() + 1);
                    renderScheduleCalendar();
                });
            }
            if (btnToday) {
                btnToday.addEventListener('click', () => {
                    calendarDateState = new Date();
                    renderScheduleCalendar();
                });
            }

            // Bind click events on schedule chips
            calendarContainer.querySelectorAll('.schedule-chip').forEach(chip => {
                chip.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const classId = parseInt(chip.getAttribute('data-class-id'));
                    const evId = chip.getAttribute('data-ev-id');
                    const ev = cachedScheduleEvents.find(item => item.id === evId);
                    if (ev && classId) {
                        openClassDetailModal(classId, ev);
                    }
                });
            });
        }

        // 2. My Classes Tab
        async function loadMyClassesData() {
            const container = document.getElementById('my-classes-list');
            if (!container) return;

            container.innerHTML = `
                <div class="text-center py-5 col-span-3">
                    <i class="fa fa-spinner fa-spin fa-2x text-primary"></i>
                    <p class="mt-2 text-muted">Đang tải các lớp học của bạn...</p>
                </div>
            `;

            try {
                const res = await fetch('/student/api/my-classes');
                const data = await res.json();

                if (data.status === 'success') {
                    state.my_classes = data.my_classes;
                    renderMyClasses();
                } else {
                    container.innerHTML = `<div class="text-center py-5 col-span-3 text-danger"><p>${data.message || 'Không thể tải danh sách lớp học.'}</p></div>`;
                }
            } catch (err) {
                console.error("My classes fetch error:", err);
                container.innerHTML = `<div class="text-center py-5 col-span-3 text-danger"><p>Lỗi kết nối mạng.</p></div>`;
            }
        }

        function renderMyClasses() {
            const container = document.getElementById('my-classes-list');
            if (!container) return;

            if (state.my_classes.length === 0) {
                container.innerHTML = `
                    <div class="card col-span-3 text-center py-5">
                        <div class="card-body">
                            <i class="fa fa-graduation-cap fa-3x text-muted mb-4"></i>
                            <h4 class="text-primary font-bold">Bạn chưa tham gia lớp học nào</h4>
                            <p class="text-muted mt-2">Hãy đăng ký một lớp học đang mở tuyển sinh hoặc liên hệ bộ phận tuyển sinh để được xếp lớp.</p>
                        </div>
                    </div>
                `;
                return;
            }

            container.innerHTML = '';
            state.my_classes.forEach(cls => {
                const attPct = cls.attendance_total > 0 
                    ? Math.round((cls.attendance_present / cls.attendance_total) * 100)
                    : 100;
                const attColor = attPct >= 80 ? '#10B981' : attPct >= 60 ? '#F59E0B' : '#EF4444';

                const card = document.createElement('div');
                card.className = 'card class-card';
                card.innerHTML = `
                    <div class="card-header bg-gradient">
                        <h3 class="text-white"><i class="fa fa-graduation-cap"></i> ${cls.class_code}</h3>
                        <span class="badge ${cls.enrollment_state === 'Đang học' ? 'badge-success' : 'badge-warning'}">${cls.enrollment_state}</span>
                    </div>
                    <div class="card-body">
                        <h4 class="class-card-title">${cls.class_name}</h4>
                        <p class="class-card-meta"><i class="fa fa-book text-primary"></i> <strong>Khóa học:</strong> ${cls.course_name}</p>
                        <p class="class-card-meta"><i class="fa fa-user-tie text-primary"></i> <strong>Giảng viên:</strong> ${cls.teacher_name}</p>
                        <p class="class-card-meta"><i class="fa fa-calendar-alt text-primary"></i> <strong>Lịch học:</strong> ${cls.schedule || 'Chưa xếp lịch'}</p>
                        <p class="class-card-meta"><i class="fa fa-door-open text-primary"></i> <strong>Phòng học:</strong> ${cls.classroom || '---'}</p>
                        <div style="margin-top:14px; padding-top:14px; border-top:1px solid #E2E8F0;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <span style="font-size:13px; color:#64748B;">Chuyên cần của bạn</span>
                                <span style="font-weight:700; color:${attColor};">${cls.attendance_rate}</span>
                            </div>
                            <div style="height:8px; background:#E2E8F0; border-radius:4px; overflow:hidden;">
                                <div style="height:100%; width:${attPct}%; background:${attColor}; border-radius:4px; transition:width 0.5s;"></div>
                            </div>
                            <div style="font-size:12px; color:#64748B; margin-top:4px;">${cls.attendance_present}/${cls.attendance_total} buổi có mặt</div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <button class="btn btn-primary btn-block btn-view-class-detail" data-class-id="${cls.id}" data-class-idx="${state.my_classes.indexOf(cls)}">
                            <i class="fa fa-eye"></i> Xem Chi tiết &amp; Điểm danh
                        </button>
                    </div>
                `;
                container.appendChild(card);
            });

            // Bind click detail buttons
            container.querySelectorAll('.btn-view-class-detail').forEach(btn => {
                btn.addEventListener('click', () => {
                    const classId = parseInt(btn.getAttribute('data-class-id'));
                    const idx = parseInt(btn.getAttribute('data-class-idx'));
                    openClassDetailModal(classId, state.my_classes[idx]);
                });
            });
        }

        async function openClassDetailModal(classId, cls) {
            const modal = document.getElementById('class-detail-modal');
            const modalName = document.getElementById('modal-class-name');
            const modalCode = document.getElementById('modal-class-code');
            const modalInfo = document.getElementById('modal-class-info');
            const modalSummary = document.getElementById('modal-attendance-summary');
            const modalBody = document.getElementById('modal-attendance-body');

            if (!modal) return;

            // Populate header
            if (modalName) modalName.textContent = cls.class_name;
            if (modalCode) modalCode.textContent = `Mã lớp: ${cls.class_code} | Mã phiếu: ${cls.enrollment_code || ''}`;

            // Populate info grid
            if (modalInfo) {
                modalInfo.innerHTML = [
                    { icon: 'fa-book', label: 'Khóa học', value: cls.course_name },
                    { icon: 'fa-user-tie', label: 'Giảng viên', value: cls.teacher_name },
                    { icon: 'fa-calendar-alt', label: 'Lịch học', value: cls.schedule || 'Chưa xếp lịch' },
                    { icon: 'fa-door-open', label: 'Phòng học', value: cls.classroom || '---' },
                    { icon: 'fa-play-circle', label: 'Khai giảng', value: formatDate(cls.start_date) },
                    { icon: 'fa-stop-circle', label: 'Kết thúc', value: formatDate(cls.end_date) || 'Chưa xác định' },
                ].map(item => `
                    <div style="display:flex; align-items:center; gap:10px;">
                        <div style="width:36px; height:36px; background:#EFF4FC; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                            <i class="fa ${item.icon}" style="color:#0C2B5C;"></i>
                        </div>
                        <div>
                            <div style="font-size:11px; color:#64748B; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">${item.label}</div>
                            <div style="font-size:14px; font-weight:600; color:#1A2530;">${item.value}</div>
                        </div>
                    </div>
                `).join('');
            }

            // Show loading in attendance table
            if (modalSummary) modalSummary.innerHTML = '';
            if (modalBody) {
                modalBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:24px; color:#64748B;"><i class="fa fa-spinner fa-spin"></i> Đang tải...</td></tr>`;
            }

            // Show modal
            modal.style.display = 'flex';

            // Fetch attendance
            try {
                const res = await fetch(`/student/api/class-attendance?class_id=${classId}`);
                const data = await res.json();

                if (data.status === 'success') {
                    const attList = data.attendance;
                    const total = attList.length;
                    const present = attList.filter(a => a.status === 'present' || a.status === 'late').length;
                    const absent = attList.filter(a => a.status === 'absent').length;
                    const permission = attList.filter(a => a.status === 'permission').length;
                    const rate = total > 0 ? Math.round((present / total) * 100) : 100;
                    const attColor = rate >= 80 ? '#10B981' : rate >= 60 ? '#F59E0B' : '#EF4444';

                    // Summary stats
                    if (modalSummary) {
                        modalSummary.innerHTML = [
                            { label: 'Tổng buổi', value: total, color: '#0C2B5C', bg: '#EFF4FC' },
                            { label: 'Có mặt', value: present, color: '#10B981', bg: '#E6FDF4' },
                            { label: 'Vắng', value: absent, color: '#EF4444', bg: '#FEF2F2' },
                            { label: 'Phép', value: permission, color: '#3B82F6', bg: '#EFF6FF' },
                            { label: 'Chuyên cần', value: `${rate}%`, color: attColor, bg: '#F8FAFC' },
                        ].map(s => `
                            <div style="flex:1; background:${s.bg}; border-radius:10px; padding:12px 14px; text-align:center; min-width:70px;">
                                <div style="font-size:22px; font-weight:800; color:${s.color};">${s.value}</div>
                                <div style="font-size:11px; color:#64748B; font-weight:600; margin-top:2px;">${s.label}</div>
                            </div>
                        `).join('');
                    }

                    if (modalBody) {
                        if (attList.length === 0) {
                            modalBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:24px; color:#64748B;">Chưa có dữ liệu điểm danh cho lớp này.</td></tr>`;
                        } else {
                            modalBody.innerHTML = attList.map(att => {
                                const badgeColors = {
                                    present: { bg: '#E6FDF4', color: '#10B981' },
                                    late:    { bg: '#FFFBEB', color: '#F59E0B' },
                                    absent:  { bg: '#FEF2F2', color: '#EF4444' },
                                    permission: { bg: '#EFF6FF', color: '#3B82F6' },
                                };
                                const bc = badgeColors[att.status] || { bg: '#F8FAFC', color: '#64748B' };
                                return `
                                    <tr style="border-bottom:1px solid #E2E8F0;">
                                        <td style="padding:14px 16px; font-size:14px;">${formatDate(att.date)}</td>
                                        <td style="padding:14px 16px; font-size:14px;">Buổi số ${att.session}</td>
                                        <td style="padding:14px 16px;">
                                            <span style="background:${bc.bg}; color:${bc.color}; padding:4px 10px; border-radius:20px; font-size:12px; font-weight:700;">${att.status_label}</span>
                                        </td>
                                        <td style="padding:14px 16px; font-size:13px; color:#64748B;">${att.note || '---'}</td>
                                    </tr>
                                `;
                            }).join('');
                        }
                    }
                } else {
                    if (modalBody) modalBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:24px; color:#EF4444;">Không thể tải dữ liệu điểm danh.</td></tr>`;
                }
            } catch (err) {
                console.error("Class attendance fetch error:", err);
                if (modalBody) modalBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:24px; color:#EF4444;">Lỗi kết nối khi tải điểm danh.</td></tr>`;
            }
        }

        // Close modal on backdrop click
        const classModal = document.getElementById('class-detail-modal');
        if (classModal) {
            classModal.addEventListener('click', (e) => {
                if (e.target === classModal) classModal.style.display = 'none';
            });
        }

        // 3. Classes Tab (Open list)
        async function loadClassesData() {
            const classesContainer = document.getElementById('classes-list');
            if (!classesContainer) return;

            classesContainer.innerHTML = `
                <div class="text-center py-5 col-span-3">
                    <i class="fa fa-spinner fa-spin fa-2x text-primary"></i>
                    <p class="mt-2 text-muted">Đang tải danh sách lớp học từ Odoo...</p>
                </div>
            `;

            try {
                const res = await fetch('/student/api/classes');
                const data = await res.json();

                if (data.status === 'success') {
                    state.classes = data.classes;
                    renderClassesList();
                } else {
                    classesContainer.innerHTML = `<div class="text-center py-5 col-span-3 text-danger"><i class="fa fa-exclamation-triangle fa-2x"></i><p class="mt-2">${data.message || 'Không thể tải danh sách lớp học.'}</p></div>`;
                }
            } catch (err) {
                console.error("Classes fetch error:", err);
                classesContainer.innerHTML = `<div class="text-center py-5 col-span-3 text-danger"><i class="fa fa-wifi fa-2x"></i><p class="mt-2">Lỗi kết nối mạng!</p></div>`;
            }
        }

        function renderClassesList() {
            const classesContainer = document.getElementById('classes-list');
            if (!classesContainer) return;

            if (state.classes.length === 0) {
                classesContainer.innerHTML = `
                    <div class="card col-span-3 text-center py-5">
                        <div class="card-body">
                            <i class="fa fa-info-circle fa-3x text-muted mb-4"></i>
                            <h4 class="text-primary font-bold">Không có lớp học nào khả dụng</h4>
                            <p class="text-muted mt-2">Hiện tại không có lớp học nào đang mở tuyển sinh. Vui lòng quay lại sau.</p>
                        </div>
                    </div>
                `;
                return;
            }

            classesContainer.innerHTML = '';
            state.classes.forEach(cls => {
                const pct = Math.round((cls.current_student_count / cls.max_students) * 100);
                const isFull = cls.available_seats <= 0;
                const isGuest = !state.student;
                const isEnrolled = cls.is_enrolled;
                const isConflict = cls.is_conflict;

                let badgeHtml = `<span class="badge ${isFull ? 'badge-danger' : 'badge-success'}">${isFull ? 'Hết Chỗ' : 'Đang Tuyển'}</span>`;
                let buttonHtml = '';

                if (isEnrolled) {
                    badgeHtml = `<span class="badge badge-success" style="background:#10B981; color:#FFF;"><i class="fa fa-check-circle"></i> Đã Đăng Ký</span>`;
                    buttonHtml = `<button class="btn btn-secondary btn-block" disabled style="opacity:0.8;"><i class="fa fa-check-circle"></i> Đã Đăng Ký Lớp Này</button>`;
                } else if (isConflict) {
                    badgeHtml = `<span class="badge badge-warning" style="background:#F59E0B; color:#FFF;" title="${cls.conflict_reason}"><i class="fa fa-exclamation-triangle"></i> Trùng Lịch Học</span>`;
                    buttonHtml = `<button class="btn btn-block" disabled style="background:#FEF2F2; color:#DC2626; border:1px solid #FCA5A5; font-weight:600;" title="${cls.conflict_reason}"><i class="fa fa-ban"></i> Không Thể Đăng Ký (Trùng Lịch)</button>`;
                } else if (isFull) {
                    buttonHtml = `<button class="btn btn-outline btn-block" disabled>Lớp Đã Đầy Chỗ</button>`;
                } else if (isGuest) {
                    buttonHtml = `<button class="btn btn-secondary btn-block btn-enroll" data-class-id="${cls.id}"><i class="fa fa-headset"></i> Đăng Ký Tư Vấn Lớp</button>`;
                } else {
                    buttonHtml = `<button class="btn btn-primary btn-block btn-enroll" data-class-id="${cls.id}"><i class="fa fa-paper-plane"></i> Đăng Ký Học Ngay</button>`;
                }

                const card = document.createElement('div');
                card.className = 'card class-card';
                card.innerHTML = `
                    <div class="card-header bg-gradient">
                        <h3 class="text-white"><i class="fa fa-school"></i> ${cls.class_code}</h3>
                        ${badgeHtml}
                    </div>
                    <div class="card-body">
                        <h4 class="class-card-title">${cls.class_name}</h4>
                        <p class="class-card-meta"><i class="fa fa-book text-primary"></i> <strong>Khóa học:</strong> ${cls.course_name}</p>
                        <p class="class-card-meta"><i class="fa fa-user-tie text-primary"></i> <strong>Giảng viên:</strong> ${cls.teacher_name}</p>
                        <p class="class-card-meta"><i class="fa fa-calendar-alt text-primary"></i> <strong>Lịch học:</strong> ${cls.schedule || 'Chưa xếp lịch'}</p>
                        <p class="class-card-meta"><i class="fa fa-clock text-primary"></i> <strong>Khai giảng:</strong> ${formatDate(cls.start_date)}</p>
                        <p class="class-card-meta"><i class="fa fa-door-open text-primary"></i> <strong>Phòng học:</strong> ${cls.classroom || '---'}</p>
                        
                        ${isConflict ? `
                            <div class="vus-alert-box warning my-2" style="padding: 10px 14px; margin: 8px 0; border-radius: 8px;">
                                <div class="alert-icon" style="width: 28px; height: 28px; font-size: 13px; border-radius: 6px;"><i class="fa fa-exclamation-triangle"></i></div>
                                <div class="alert-content">
                                    <div class="alert-message" style="font-size: 12px; font-weight: 600; color: #92400E;">${cls.conflict_reason}</div>
                                </div>
                            </div>
                        ` : ''}

                        <div class="progress-container mt-2">
                            <div class="progress-label">
                                <span>Sĩ số lớp</span>
                                <span>${cls.current_student_count}/${cls.max_students} học viên</span>
                            </div>
                            <div class="progress-bar-bg">
                                <div class="progress-bar-fill" style="width: ${pct}%"></div>
                            </div>
                        </div>

                        <div class="class-card-price text-right mt-2">
                            ${formatCurrency(cls.price)}
                        </div>
                    </div>
                    <div class="card-footer">
                        ${buttonHtml}
                    </div>
                `;
                classesContainer.appendChild(card);
            });

            // Add action listener to enroll buttons
            classesContainer.querySelectorAll('.btn-enroll').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const classId = btn.getAttribute('data-class-id');
                    if (!state.student) {
                        const targetClass = state.classes.find(c => c.id === parseInt(classId));
                        switchTab('consult');
                        const consultNotes = document.getElementById('consult_notes');
                        if (consultNotes) consultNotes.value = `Tôi quan tâm đến lớp học: ${targetClass.class_name} (${targetClass.class_code}).`;
                        if (targetClass.course_id && consultCourseSelect) {
                            consultCourseSelect.value = targetClass.course_id;
                        }
                    } else {
                        enrollClass(classId);
                    }
                });
            });
        }

        async function enrollClass(classId) {
            try {
                const res = await fetch('/student/api/enroll', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ class_id: classId })
                });
                const text = await res.text();
                let data;
                try {
                    data = JSON.parse(text);
                } catch (jsonErr) {
                    console.error("Non-JSON response from server:", text);
                    showToast('Hệ thống trả về phản hồi không hợp lệ!', 'error');
                    return;
                }
                if (data.status === 'success') {
                    showToast(data.message, 'success');
                    loadClassesData();
                } else {
                    showToast(data.message || 'Lỗi khi đăng ký lớp học!', 'error');
                }
            } catch (err) {
                console.error("Enrollment failed:", err);
                showToast('Lỗi kết nối, vui lòng thử lại!', 'error');
            }
        }

        // 4. Tuition & Payment Tab
        async function loadTuitionData() {
            if (!state.student) return;

            const tableBody = document.getElementById('invoices-table-body');
            const reminderText = document.getElementById('tuition-reminder-text');
            const reminderBanner = document.getElementById('tuition-reminder-banner');

            if (!tableBody) return;

            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4">
                        <i class="fa fa-spinner fa-spin text-primary"></i> Đang tải dữ liệu học phí...
                    </td>
                </tr>
            `;

            try {
                const res = await fetch('/student/api/invoices');
                const data = await res.json();

                if (data.status === 'success') {
                    state.invoices = data.invoices;
                    renderInvoicesTable();

                    // Calculate unpaid tuition & find nearest due date for reminder banner
                    let totalUnpaid = 0;
                    let unpaidCount = 0;
                    let nearestDue = '';
                    let draftCount = 0;

                    state.invoices.forEach(inv => {
                        if (inv.state === 'draft' || (inv.payment_state && inv.payment_state.includes('Nháp'))) {
                            draftCount++;
                        }
                        if (inv.payment_state === 'Chờ thanh toán' || inv.state === 'confirmed') {
                            totalUnpaid += inv.amount;
                            unpaidCount++;
                            if (inv.due_date && (!nearestDue || inv.due_date < nearestDue)) {
                                nearestDue = inv.due_date;
                            }
                        }
                    });

                    // Dynamic Reminder Text
                    if (reminderText && reminderBanner) {
                        reminderBanner.style.display = 'flex';
                        if (totalUnpaid > 0) {
                            const dueInfo = nearestDue ? ` (Hạn đóng gần nhất: <strong>${formatDate(nearestDue)}</strong>)` : '';
                            reminderText.innerHTML = `⚠️ Bạn đang có <strong>${unpaidCount}</strong> khoản học phí chưa thanh toán với tổng số tiền <strong>${formatCurrency(totalUnpaid)}</strong>${dueInfo}. Vui lòng nhấp vào nút <strong>Mã QR</strong> ở dòng tương ứng để quét mã VietQR chuyển khoản trước thời hạn.`;
                            reminderBanner.style.background = 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)';
                            reminderBanner.style.borderColor = '#F59E0B';
                        } else if (draftCount > 0) {
                            reminderText.innerHTML = `ℹ️ Bạn có <strong>${draftCount}</strong> yêu cầu đăng ký lớp học đang chờ tư vấn viên VUS kiểm tra và tạo hóa đơn. Bạn có thể nhấn nút <strong>Hủy phiếu</strong> nếu thay đổi quyết định trước khi được xác nhận.`;
                            reminderBanner.style.background = 'linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)';
                            reminderBanner.style.borderColor = '#3B82F6';
                        } else {
                            reminderText.innerHTML = `✅ Bạn đã hoàn thành đầy đủ nghĩa vụ học phí cho tất cả các lớp đã đăng ký. Cảm ơn bạn đã đồng hành cùng VUS!`;
                            reminderBanner.style.background = 'linear-gradient(135deg, #E6FDF4 0%, #D1FAE5 100%)';
                            reminderBanner.style.borderColor = '#10B981';
                        }
                    }

                    // Auto-select ONLY payable invoices ('Chờ thanh toán' state)
                    const payableInvoices = state.invoices.filter(inv => inv.payment_state === 'Chờ thanh toán' || inv.state === 'confirmed');
                    if (payableInvoices.length > 0) {
                        selectInvoiceForPayment(payableInvoices[0]);
                    } else {
                        state.selected_invoice = null;
                        const titleEl = document.getElementById('selected-inv-title');
                        const subEl = document.getElementById('selected-inv-subtitle');
                        const vnpayAmtEl = document.getElementById('vnpay-amount-text');
                        const syntaxEl = document.getElementById('payment-syntax');
                        const qrImage = document.getElementById('payment-qr');

                        if (titleEl) titleEl.innerHTML = `<i class="fa fa-info-circle"></i> KHÔNG CÓ HỌC PHÍ CẦN NỘP`;
                        if (subEl) subEl.textContent = `Không có phiếu nào ở trạng thái Chờ thanh toán`;
                        if (vnpayAmtEl) vnpayAmtEl.textContent = `0 đ`;
                        if (syntaxEl) syntaxEl.innerHTML = `VUS PAY [Mã_Phiếu]`;
                        if (qrImage) qrImage.src = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=NO-PAYMENT-DUE`;
                    }

                    // Bind Copy Memo Button
                    const copyMemoBtn = document.getElementById('btn-copy-memo');
                    if (copyMemoBtn) {
                        copyMemoBtn.onclick = () => {
                            const syntaxEl = document.getElementById('payment-syntax');
                            if (syntaxEl) {
                                // Extract first line (the code)
                                const memoText = syntaxEl.innerText.split('\n')[0].trim();
                                navigator.clipboard.writeText(memoText).then(() => {
                                    showToast(`Đã chép nội dung: ${memoText}`, 'success');
                                }).catch(err => {
                                    console.error("Copy failed:", err);
                                });
                            }
                        };
                    }
                } else {
                    tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">${data.message || 'Không thể tải học phí.'}</td></tr>`;
                }
            } catch (err) {
                console.error("Tuition fetch error:", err);
                tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Lỗi kết nối máy chủ.</td></tr>`;
            }
        }

        // Global helper to switch payment method tabs in Checkout Console
        window.switchPayMethod = function(method) {
            const btnVietQr = document.getElementById('btn-tab-vietqr');
            const btnVnPay = document.getElementById('btn-tab-vnpay');
            const paneVietQr = document.getElementById('pay-pane-vietqr');
            const paneVnPay = document.getElementById('pay-pane-vnpay');

            if (!btnVietQr || !btnVnPay || !paneVietQr || !paneVnPay) return;

            if (method === 'vnpay') {
                btnVietQr.classList.remove('active');
                btnVnPay.classList.add('active');
                paneVietQr.style.display = 'none';
                paneVnPay.style.display = 'block';
            } else {
                btnVnPay.classList.remove('active');
                btnVietQr.classList.add('active');
                paneVnPay.style.display = 'none';
                paneVietQr.style.display = 'block';
            }
        };

        function selectInvoiceForPayment(inv) {
            // ONLY allow payment details for 'Chờ thanh toán' / confirmed enrollments
            const isPayable = (inv.payment_state === 'Chờ thanh toán') || (inv.state === 'confirmed');
            if (!isPayable) {
                showToast(`Phiếu ${inv.enrollment_code} ở trạng thái "${inv.payment_state}", không cần thanh toán.`, 'info');
                return;
            }

            state.selected_invoice = inv;

            const syntaxEl = document.getElementById('payment-syntax');
            const qrImage = document.getElementById('payment-qr');
            const titleEl = document.getElementById('selected-inv-title');
            const subEl = document.getElementById('selected-inv-subtitle');
            const vnpayAmtEl = document.getElementById('vnpay-amount-text');
            const demoVnPayBtn = document.getElementById('btn-demo-vnpay');

            if (titleEl) titleEl.innerHTML = `<i class="fa fa-credit-card"></i> PHIẾU: ${inv.enrollment_code}`;
            if (subEl) subEl.textContent = `${inv.course_name} (${formatCurrency(inv.amount)})`;
            if (vnpayAmtEl) vnpayAmtEl.textContent = formatCurrency(inv.amount);

            // Format syntax: VUS PAY [EnrollmentCode]
            const memo = `VUS PAY ${inv.enrollment_code}`;
            if (syntaxEl) {
                syntaxEl.innerHTML = `<strong>${memo}</strong><br/><span style="font-size: 13px; font-weight: normal; color: var(--text-muted); display: block; margin-top: 5px;">Số tiền: <strong class="text-primary">${formatCurrency(inv.amount)}</strong></span>`;
            }
            
            if (qrImage) {
                const vietQrUrl = `https://img.vietqr.io/image/VCB-1014567899-qr_only.png?amount=${inv.amount}&addInfo=${encodeURIComponent(memo)}&accountName=ANH%20VAN%20HOI%20VIET%20MY`;
                qrImage.src = vietQrUrl;
            }

            const vnpayQrImg = document.getElementById('vnpay-qr-img');
            if (vnpayQrImg) {
                vnpayQrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=VNPAY_DEMO_GATEWAY_${encodeURIComponent(inv.enrollment_code)}_${inv.amount}`;
            }

            // Highlight chosen row & check radio
            document.querySelectorAll('#invoices-table-body tr').forEach(row => {
                row.classList.remove('selected-payment-row');
                const radio = row.querySelector('.select-inv-radio');
                const rowCode = row.getAttribute('data-code');
                if (rowCode === inv.enrollment_code) {
                    row.classList.add('selected-payment-row');
                    if (radio) radio.checked = true;
                } else {
                    if (radio) radio.checked = false;
                }
            });

            // Bind Instant Demo VNPay payment button
            if (demoVnPayBtn) {
                demoVnPayBtn.onclick = () => {
                    showConfirmModal({
                        title: 'Xác nhận thanh toán',
                        message: `Bạn có muốn mô phỏng thanh toán VNPay số tiền ${formatCurrency(inv.amount)} cho phiếu ${inv.enrollment_code}?`,
                        icon: 'fa-bolt',
                        iconBg: '#ECFDF5',
                        iconColor: '#059669',
                        confirmText: 'Thanh toán ngay',
                        confirmBtnClass: 'btn-primary',
                        onConfirm: async () => {
                            try {
                                showToast(`Đang xử lý thanh toán demo qua VNPay...`, 'info');
                                const res = await fetch('/student/api/vnpay/simulate', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ enrollment_id: inv.id })
                                });
                                const data = await res.json();
                                if (data.status === 'success') {
                                    showToast(data.message, 'success');
                                    loadTuitionData();
                                    loadOverviewData();
                                    loadMyClassesData();
                                } else {
                                    showToast(data.message || 'Lỗi xử lý thanh toán demo!', 'error');
                                }
                            } catch (err) {
                                console.error("Simulate payment error:", err);
                                showToast('Lỗi hệ thống khi thanh toán demo!', 'error');
                            }
                        }
                    });
                };
            }
        }

        function renderInvoicesTable() {
            const tableBody = document.getElementById('invoices-table-body');
            const countBadge = document.getElementById('invoice-count-badge');
            if (countBadge) countBadge.textContent = `${state.invoices.length} phiếu`;

            if (!tableBody) return;

            if (state.invoices.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center py-4 text-muted">
                            Bạn chưa đăng ký khóa học nào! Hãy chọn một lớp học mở tuyển sinh để tiến hành đăng ký.
                        </td>
                    </tr>
                `;
                return;
            }

            tableBody.innerHTML = '';
            state.invoices.forEach(inv => {
                let badgeClass = 'badge-warning';
                if (inv.payment_state === 'Đã thanh toán') {
                    badgeClass = 'badge-success';
                } else if (inv.payment_state === 'Chờ thanh toán') {
                    badgeClass = 'badge-warning';
                } else if (inv.payment_state.includes('Nháp') || inv.state === 'draft') {
                    badgeClass = 'badge-info';
                } else if (inv.payment_state === 'Đã hủy' || inv.state === 'cancel') {
                    badgeClass = 'badge-danger';
                }

                const isPayable = (inv.payment_state === 'Chờ thanh toán') || (inv.state === 'confirmed');
                const isDraft = (inv.state === 'draft') || (inv.payment_state && inv.payment_state.includes('Nháp'));
                const isPaid = (inv.payment_state === 'Đã thanh toán') || (inv.state === 'paid');
                const isCancelled = (inv.state === 'cancel') || (inv.payment_state === 'Đã hủy');

                // Selector cell rendering (ONLY show active radio for Chờ thanh toán)
                let selectorCellHtml = '';
                if (isPayable) {
                    selectorCellHtml = `<input type="radio" name="selected_invoice_radio" class="select-inv-radio" data-code="${inv.enrollment_code}" title="Chọn phiếu này để thanh toán"/>`;
                } else if (isDraft) {
                    selectorCellHtml = `<small class="text-muted" title="Đang chờ duyệt">Chờ duyệt</small>`;
                } else if (isPaid) {
                    selectorCellHtml = `<i class="fa fa-check-circle text-success" title="Đã hoàn thành thanh toán"></i>`;
                } else {
                    selectorCellHtml = `<i class="fa fa-times-circle text-danger" title="Đã hủy"></i>`;
                }

                // Action buttons
                let actionBtnHtml = '';
                if (isDraft) {
                    actionBtnHtml = `
                        <button class="btn btn-outline btn-sm btn-cancel-enroll" data-id="${inv.id}" title="Hủy yêu cầu đăng ký chưa xác nhận này" style="color: #EF4444; border: 1.5px solid #EF4444; padding: 3px 10px; font-size: 12px; background: transparent; cursor: pointer; border-radius: 6px;">
                            <i class="fa fa-trash-alt"></i> Hủy phiếu
                        </button>
                    `;
                }

                let payBtnHtml = '';
                if (isPayable) {
                    payBtnHtml = `
                        <button class="btn btn-primary btn-sm btn-pay-invoice" data-code="${inv.enrollment_code}" title="Xem mã VietQR &amp; VNPay" style="padding: 3px 10px; font-size: 12px; border-radius: 6px;">
                            <i class="fa fa-qrcode"></i> Thanh toán
                        </button>
                    `;
                }

                // Format Due Date with status styling
                let dueDateHtml = formatDate(inv.due_date) || 'Theo khai giảng';
                if (isPayable && inv.due_date) {
                    const todayStr = new Date().toISOString().split('T')[0];
                    if (inv.due_date < todayStr) {
                        dueDateHtml = `<span class="text-danger font-bold" title="Đã quá hạn thanh toán"><i class="fa fa-exclamation-circle"></i> ${formatDate(inv.due_date)} (Quá hạn)</span>`;
                    } else {
                        dueDateHtml = `<span class="font-bold text-primary"><i class="fa fa-clock"></i> ${formatDate(inv.due_date)}</span>`;
                    }
                }

                const row = document.createElement('tr');
                row.setAttribute('data-code', inv.enrollment_code);
                if (isPayable) row.style.cursor = 'pointer';
                row.innerHTML = `
                    <td style="text-align: center;">
                        ${selectorCellHtml}
                    </td>
                    <td><strong>${inv.enrollment_code}</strong></td>
                    <td>
                        <div><strong>${inv.course_name}</strong></div>
                        <small class="text-muted"><i class="fa fa-school"></i> Lớp: ${inv.class_name}</small>
                    </td>
                    <td class="font-bold text-primary">${formatCurrency(inv.amount)}</td>
                    <td>${dueDateHtml}</td>
                    <td>
                        <span class="badge ${badgeClass}">${inv.payment_state}</span>
                    </td>
                    <td style="text-align: right;">
                        ${payBtnHtml}
                        ${actionBtnHtml}
                    </td>
                `;

                // Row click handler
                row.addEventListener('click', (e) => {
                    if (e.target.closest('.btn-cancel-enroll')) return;
                    if (isPayable) {
                        selectInvoiceForPayment(inv);
                    } else if (isDraft) {
                        showToast(`Phiếu ${inv.enrollment_code} đang chờ tư vấn viên duyệt, chưa tạo mã thanh toán.`, 'info');
                    } else if (isPaid) {
                        showToast(`Phiếu ${inv.enrollment_code} đã thanh toán thành công!`, 'success');
                    }
                });

                tableBody.appendChild(row);
            });

            // Bind QR pay buttons
            tableBody.querySelectorAll('.btn-pay-invoice').forEach(btn => {
                btn.addEventListener('click', () => {
                    const code = btn.getAttribute('data-code');
                    const inv = state.invoices.find(i => i.enrollment_code === code);
                    if (inv) {
                        selectInvoiceForPayment(inv);
                        showToast(`Đã tải mã VietQR thanh toán cho phiếu ${code}`, 'info');
                    }
                });
            });

            // Bind cancel buttons
            tableBody.querySelectorAll('.btn-cancel-enroll').forEach(btn => {
                btn.addEventListener('click', () => {
                    const enrId = btn.getAttribute('data-id');
                    showConfirmModal({
                        title: 'Xác nhận hủy phiếu ghi danh',
                        message: 'Bạn có chắc chắn muốn hủy đăng ký lớp học chưa xác nhận này? Yêu cầu sẽ bị hủy và giải phóng chỗ trống cho học viên khác.',
                        icon: 'fa-trash-alt',
                        iconBg: '#FEF2F2',
                        iconColor: '#DC2626',
                        confirmText: 'Hủy phiếu ngay',
                        confirmBtnClass: 'btn-secondary',
                        onConfirm: async () => {
                            try {
                                const res = await fetch('/student/api/enroll/cancel', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ enrollment_id: enrId })
                                });
                                const data = await res.json();
                                if (data.status === 'success') {
                                    showToast(data.message, 'success');
                                    loadTuitionData();
                                    loadOverviewData();
                                } else {
                                    showToast(data.message || 'Lỗi khi hủy đăng ký!', 'error');
                                }
                            } catch (err) {
                                console.error("Cancel enrollment failed:", err);
                                showToast('Lỗi kết nối, vui lòng thử lại!', 'error');
                            }
                        }
                    });
                });
            });
        }

        // 5. Attendance / Chuyên cần Tab
        async function loadAttendanceData() {
            if (!state.student) return;

            const tableBody = document.getElementById('attendance-table-body');
            if (!tableBody) return;

            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4">
                        <i class="fa fa-spinner fa-spin text-primary"></i> Đang tải dữ liệu điểm danh...
                    </td>
                </tr>
            `;

            try {
                const res = await fetch('/student/api/attendance');
                const data = await res.json();

                if (data.status === 'success') {
                    state.attendance = data.attendance;
                    renderAttendanceTable();
                } else {
                    tableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">${data.message || 'Không thể tải dữ liệu điểm danh.'}</td></tr>`;
                }
            } catch (err) {
                console.error("Attendance fetch error:", err);
                tableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">Lỗi kết nối điểm danh.</td></tr>`;
            }
        }

        function renderAttendanceTable() {
            const tableBody = document.getElementById('attendance-table-body');
            if (!tableBody) return;

            if (state.attendance.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center py-4 text-muted">
                            Chưa có lịch sử điểm danh nào được ghi nhận cho bạn.
                        </td>
                    </tr>
                `;
                return;
            }

            tableBody.innerHTML = '';
            state.attendance.forEach(att => {
                let badgeClass = 'badge-success';
                if (att.status === 'absent') badgeClass = 'badge-danger';
                if (att.status === 'late') badgeClass = 'badge-warning';
                if (att.status === 'permission') badgeClass = 'badge-info';

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(att.date)}</td>
                    <td><strong>${att.class_name}</strong></td>
                    <td>Buổi số ${att.session}</td>
                    <td><span class="badge ${badgeClass}">${att.status_label}</span></td>
                    <td><span class="text-muted italic">${att.note || '---'}</span></td>
                `;
                tableBody.appendChild(row);
            });
        }

        // 6. Consultation Form Tab
        async function loadConsultationData() {
            const selectEl = document.getElementById('consult_campaign') || consultCourseSelect;
            if (!selectEl) return;

            // Fetch campaigns list if not already cached
            if (!state.campaigns || state.campaigns.length === 0) {
                try {
                    const res = await fetch('/student/api/campaigns');
                    const data = await res.json();
                    if (data.status === 'success') {
                        state.campaigns = data.campaigns;
                        populateConsultCampaigns();
                    }
                } catch (err) {
                    console.error("Failed to load campaigns for consult form dropdown:", err);
                }
            } else {
                populateConsultCampaigns();
            }

            // Auto-fill logged-in student info if available
            if (state.student) {
                const cName = document.getElementById('consult_name');
                const cPhone = document.getElementById('consult_phone');
                const cEmail = document.getElementById('consult_email');
                if (cName) cName.value = state.student.name;
                if (cPhone) cPhone.value = state.student.phone || '';
                if (cEmail) cEmail.value = state.student.email || '';
            }
        }

        function populateConsultCampaigns() {
            const selectEl = document.getElementById('consult_campaign') || consultCourseSelect;
            if (!selectEl) return;
            selectEl.innerHTML = '<option value="">-- Chọn chương trình / chiến dịch chiêu sinh --</option>';
            if (state.campaigns && state.campaigns.length > 0) {
                state.campaigns.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.textContent = `${c.name} (${c.code})`;
                    selectEl.appendChild(opt);
                });
            }
        }

        async function handleConsultSubmit(e) {
            e.preventDefault();
            
            const name = document.getElementById('consult_name').value.trim();
            const phone = document.getElementById('consult_phone').value.trim();
            const email = document.getElementById('consult_email').value.trim();
            const selectEl = document.getElementById('consult_campaign') || consultCourseSelect;
            const campaign_id = selectEl ? selectEl.value : '';
            const notes = document.getElementById('consult_notes').value.trim();

            if (!name || !phone) {
                showToast('Họ tên và Số điện thoại là bắt buộc!', 'warning');
                return;
            }

            try {
                const res = await fetch('/student/api/consult', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, phone, email, campaign_id, notes })
                });
                const data = await res.json();

                if (data.status === 'success') {
                    showToast(data.message, 'success');
                    document.getElementById('consult_notes').value = '';
                    
                    if (state.student) {
                        switchTab('overview');
                    } else {
                        setTimeout(() => {
                            document.getElementById('consult_name').value = '';
                            document.getElementById('consult_phone').value = '';
                            document.getElementById('consult_email').value = '';
                            if (selectEl) selectEl.value = '';
                            
                            loginScreen.style.display = 'flex';
                            portalScreen.style.display = 'none';
                        }, 2500);
                    }
                } else {
                    showToast(data.message || 'Lỗi khi gửi yêu cầu tư vấn!', 'error');
                }
            } catch (err) {
                console.error("Consult submit error:", err);
                showToast('Lỗi kết nối máy chủ!', 'error');
            }
        }
    }

    // Bulletproof document ready checking to guarantee execution
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPortal);
    } else {
        initPortal();
    }
})();
