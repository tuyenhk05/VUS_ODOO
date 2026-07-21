# -*- coding: utf-8 -*-
import json
import logging
import re
from datetime import timedelta
from odoo import http, fields, _
from odoo.http import request

_logger = logging.getLogger(__name__)

def parse_schedule_days(sched_str):
    """
    Extract set of day-of-week indices (0=Mon, 1=Tue, ..., 6=Sun) from a schedule text string.
    Safely strips out times (e.g. 18:00) and shift names (e.g. Ca 1) to avoid false matches.
    """
    if not sched_str:
        return set()
    s_lower = str(sched_str).lower()
    
    # Clean out times like 18:00, 19.30, 18h00, 8:00-9:30
    clean_text = re.sub(r'\d{1,2}\s*[:.h]\s*\d{2}', ' ', s_lower)
    # Clean out shift numbers like ca 1, ca 2
    clean_text = re.sub(r'\bca\s*\d+\b', ' ', clean_text)
    
    dows = set()
    if 'thứ 2' in clean_text or 't2' in clean_text or 'mon' in clean_text:
        dows.add(0)
    if 'thứ 3' in clean_text or 't3' in clean_text or 'tue' in clean_text:
        dows.add(1)
    if 'thứ 4' in clean_text or 't4' in clean_text or 'wed' in clean_text:
        dows.add(2)
    if 'thứ 5' in clean_text or 't5' in clean_text or 'thu' in clean_text:
        dows.add(3)
    if 'thứ 6' in clean_text or 't6' in clean_text or 'fri' in clean_text:
        dows.add(4)
    if 'thứ 7' in clean_text or 't7' in clean_text or 'sat' in clean_text:
        dows.add(5)
    if 'chủ nhật' in clean_text or 'cn' in clean_text or 'thứ 8' in clean_text or 't8' in clean_text or 'sun' in clean_text:
        dows.add(6)
        
    return dows

def parse_schedule_time_range(sched_str):
    """
    Extract start and end minutes from midnight from a schedule text string.
    Returns (start_minutes, end_minutes). If no valid time pair found, returns (0, 1440).
    """
    if not sched_str:
        return (0, 1440)
    
    times = re.findall(r'(\d{1,2})[\s:.h]+(\d{2})', str(sched_str))
    if len(times) >= 2:
        h1, m1 = int(times[0][0]), int(times[0][1])
        h2, m2 = int(times[1][0]), int(times[1][1])
        start_min = h1 * 60 + m1
        end_min = h2 * 60 + m2
        if 0 <= start_min < end_min <= 1440:
            return (start_min, end_min)
            
    return (0, 1440)

def check_classes_overlap(cls1, cls2):
    """
    Check if two vus.class records overlap in schedule.
    Returns (is_conflict, reason_string)
    """
    if not cls1 or not cls2 or cls1.id == cls2.id:
        return False, ''

    # 1. Date Range Overlap Check
    start1 = cls1.start_date
    end1 = cls1.end_date or (start1 + timedelta(days=90)) if start1 else False
    start2 = cls2.start_date
    end2 = cls2.end_date or (start2 + timedelta(days=90)) if start2 else False

    if start1 and start2 and end1 and end2:
        if start1 > end2 or end1 < start2:
            return False, '' # Classes run during different date periods

    # 2. Days of Week Check
    days1 = set()
    if hasattr(cls1, 'time_slot_id') and cls1.time_slot_id and hasattr(cls1.time_slot_id, 'days_group') and cls1.time_slot_id.days_group:
        dg = cls1.time_slot_id.days_group
        if dg == 'mwf': days1 = {0, 2, 4}
        elif dg == 'tts': days1 = {1, 3, 5}
        elif dg == 'ss': days1 = {5, 6}

    if not days1:
        s1 = cls1.schedule or ''
        days1 = parse_schedule_days(s1)

    days2 = set()
    if hasattr(cls2, 'time_slot_id') and cls2.time_slot_id and hasattr(cls2.time_slot_id, 'days_group') and cls2.time_slot_id.days_group:
        dg = cls2.time_slot_id.days_group
        if dg == 'mwf': days2 = {0, 2, 4}
        elif dg == 'tts': days2 = {1, 3, 5}
        elif dg == 'ss': days2 = {5, 6}

    if not days2:
        s2 = cls2.schedule or ''
        days2 = parse_schedule_days(s2)

    # If either class does not have days specified (schedule unassigned), no schedule conflict
    if not days1 or not days2:
        return False, ''

    common_days = days1 & days2
    if not common_days:
        return False, '' # No common day of week!

    # 3. Time Slot Range Check
    s1_text = cls1.schedule or (cls1.time_slot_id.name if hasattr(cls1, 'time_slot_id') and cls1.time_slot_id else '')
    s2_text = cls2.schedule or (cls2.time_slot_id.name if hasattr(cls2, 'time_slot_id') and cls2.time_slot_id else '')

    has_t1 = bool(s1_text and re.search(r'\d{1,2}[\s:.h]+\d{2}', str(s1_text)))
    has_t2 = bool(s2_text and re.search(r'\d{1,2}[\s:.h]+\d{2}', str(s2_text)))

    if has_t1 and has_t2:
        t1_start, t1_end = parse_schedule_time_range(s1_text)
        t2_start, t2_end = parse_schedule_time_range(s2_text)
        is_time_overlap = max(t1_start, t2_start) < min(t1_end, t2_end)
        if is_time_overlap:
            return True, f"Bị trùng lịch học với lớp '{cls2.class_name}'"
        return False, ''

    return True, f"Bị trùng lịch học với lớp '{cls2.class_name}'"

class StudentPortalController(http.Controller):

    def _json_response(self, data, status=200):
        """Helper to return clean standard JSON responses."""
        headers = [
            ('Content-Type', 'application/json'),
            ('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0'),
        ]
        return request.make_response(json.dumps(data), headers=headers, status=200)

    def _get_student(self):
        """Retrieve student partner from current session."""
        student_id = request.session.get('vus_student_id')
        if not student_id:
            return None
        student = request.env['res.partner'].sudo().browse(student_id)
        if not student.exists() or not student.is_student:
            return None
        return student

    @http.route('/student/portal', type='http', auth='public', csrf=False)
    def portal_home(self, **kwargs):
        """Renders the single page application HTML."""
        return request.render('vus_student_portal.portal_home_template', {})

    @http.route('/student/api/login', type='http', auth='public', methods=['POST'], csrf=False)
    def api_login(self, **kwargs):
        """Login API using Student Code and Date of Birth."""
        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
            student_code = body.get('student_code', '').strip()
            dob_str = body.get('dob', '').strip()
        except Exception:
            return self._json_response({'status': 'error', 'message': 'Dữ liệu đầu vào không hợp lệ!'}, status=400)

        if not student_code or not dob_str:
            return self._json_response({'status': 'error', 'message': 'Vui lòng điền đầy đủ Mã học viên và Ngày sinh!'}, status=400)

        # Normalize student code: convert to uppercase, strip spaces
        normalized_code = student_code.upper().replace(" ", "")
        # Correct missing hyphen (e.g. VUS0040 -> VUS-0040)
        if normalized_code.startswith("VUS") and not normalized_code.startswith("VUS-") and len(normalized_code) > 3:
            normalized_code = "VUS-" + normalized_code[3:]

        # Query partner with is_student=True, matching code (case-insensitive) and dob
        student = request.env['res.partner'].sudo().search([
            ('is_student', '=', True),
            ('student_code', '=ilike', normalized_code),
            ('dob', '=', dob_str)
        ], limit=1)

        if not student:
            return self._json_response({'status': 'error', 'message': 'Mã học viên hoặc Ngày sinh không khớp với dữ liệu hệ thống!'}, status=401)

        # Save to session
        request.session['vus_student_id'] = student.id
        _logger.info("Student %s (%s) logged in to portal.", student.name, student.student_code)

        return self._json_response({
            'status': 'success',
            'student': {
                'id': student.id,
                'name': student.name,
                'student_code': student.student_code,
                'dob': str(student.dob),
                'email': student.email or '',
                'phone': student.phone or '',
                'status': dict(student._fields['student_status'].selection).get(student.student_status, '')
            }
        })

    @http.route('/student/api/logout', type='http', auth='public', methods=['POST'], csrf=False)
    def api_logout(self, **kwargs):
        """Logout student and clear session."""
        request.session.pop('vus_student_id', None)
        return self._json_response({'status': 'success', 'message': 'Đã đăng xuất thành công.'})

    @http.route('/student/api/info', type='http', auth='public', methods=['GET'], csrf=False)
    def api_info(self, **kwargs):
        """Get current logged-in student info."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        return self._json_response({
            'status': 'success',
            'student': {
                'id': student.id,
                'name': student.name,
                'student_code': student.student_code,
                'dob': str(student.dob) if student.dob else '',
                'email': student.email or '',
                'phone': student.phone or '',
                'status': dict(student._fields['student_status'].selection).get(student.student_status, '')
            }
        })

    @http.route('/student/api/courses', type='http', auth='public', methods=['GET'], csrf=False)
    def api_courses(self, **kwargs):
        """Get list of active courses for consultation/placement test registration."""
        courses = request.env['vus.course'].sudo().search([('state', '=', 'confirmed')])
        course_list = []
        for course in courses:
            course_list.append({
                'id': course.id,
                'code': course.code,
                'name': course.course_name,
                'level': dict(course._fields['level'].selection).get(course.level, ''),
                'base_price': course.base_price,
                'duration_weeks': course.duration_weeks,
                'sessions_per_week': course.sessions_per_week,
                'hours_per_session': course.hours_per_session,
                'description': course.description or ''
            })
        return self._json_response({'status': 'success', 'courses': course_list})

    def _get_class_schedule(self, cls):
        if not cls:
            return 'Chưa xếp lịch'
        if cls.schedule and str(cls.schedule).strip():
            return str(cls.schedule).strip()
        if hasattr(cls, 'time_slot_id') and cls.time_slot_id and cls.time_slot_id.name:
            return cls.time_slot_id.name
        return 'Thứ 2 - Thứ 4 - Thứ 6 (18:00 - 19:30)'

    def _create_manager_activities(self, res_model_name, res_id, summary, note_html):
        """Helper to create Odoo mail.activity notifications AND mail.message Inbox notifications for all Manager and System Admin users."""
        try:
            model_rec = request.env['ir.model'].sudo().search([('model', '=', res_model_name)], limit=1)
            if not model_rec:
                return

            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
            direct_link = f"{base_url}/web#id={res_id}&model={res_model_name}&view_type=form"

            # Append direct navigation button link if not already present
            if direct_link not in note_html and '/web#id=' not in note_html:
                btn_link_html = (
                    f'<p style="margin-top: 12px; margin-bottom: 4px;">'
                    f'  <a href="{direct_link}" target="_blank" style="background-color: #0C2B5C; color: #FFFFFF; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                    f'    👉 Click vào đây để xem chi tiết ({res_model_name})'
                    f'  </a>'
                    f'</p>'
                )
                note_html += btn_link_html

            activity_type = request.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)

            admin_user = request.env.ref('base.user_admin', raise_if_not_found=False)
            manager_group = request.env.ref('vus_student.group_vus_manager', raise_if_not_found=False)
            system_group = request.env.ref('base.group_system', raise_if_not_found=False)

            user_ids = set()
            if admin_user:
                user_ids.add(admin_user.id)
            user_ids.add(2)

            if manager_group:
                m_users = request.env['res.users'].sudo().search([('groups_id', 'in', [manager_group.id])])
                user_ids.update(m_users.ids)

            if system_group:
                s_users = request.env['res.users'].sudo().search([('groups_id', 'in', [system_group.id])])
                user_ids.update(s_users.ids)

            managers = request.env['res.users'].sudo().browse(list(user_ids))

            # 1. Create Systray Activities (Clock icon menu)
            for mgr in managers:
                request.env['mail.activity'].sudo().create({
                    'activity_type_id': activity_type.id if activity_type else False,
                    'summary': summary,
                    'note': note_html,
                    'user_id': mgr.id,
                    'res_id': res_id,
                    'res_model_id': model_rec.id,
                    'date_deadline': fields.Date.today()
                })

            # 2. Create Mail Message + Mail Notifications directly into Discuss Inbox ("Hộp thư đến")
            manager_partners = managers.mapped('partner_id').filtered(lambda p: p.exists())
            if manager_partners:
                subtype_rec = request.env.ref('mail.mt_comment', raise_if_not_found=False)
                
                # Create notification mail.message attached to record
                msg = request.env['mail.message'].sudo().create({
                    'model': res_model_name,
                    'res_id': res_id,
                    'message_type': 'notification',
                    'subject': summary,
                    'body': note_html,
                    'partner_ids': [(6, 0, manager_partners.ids)],
                    'subtype_id': subtype_rec.id if subtype_rec else False
                })

                # Create mail.notification for each manager partner so it shows up in Discuss Inbox
                notif_vals = []
                for p_id in manager_partners.ids:
                    notif_vals.append({
                        'mail_message_id': msg.id,
                        'res_partner_id': p_id,
                        'notification_type': 'inbox',
                        'is_read': False,
                    })
                request.env['mail.notification'].sudo().create(notif_vals)

            _logger.info("Created Systray activities & Inbox notifications for %d managers on model %s id %s", len(managers), res_model_name, res_id)
        except Exception as e:
            _logger.error("Failed to create manager activities / notifications: %s", str(e))

    @http.route('/student/api/classes', type='http', auth='public', methods=['GET'], csrf=False)
    def api_classes(self, **kwargs):
        """Get list of currently open classes for registration, marking enrolled & conflict classes."""
        student = self._get_student()
        enrolled_class_ids = set()
        enrolled_classes = []
        if student:
            my_enrs = request.env['vus.enrollment'].sudo().search([
                ('student_id', '=', student.id),
                ('state', 'in', ['draft', 'confirmed', 'paid'])
            ])
            enrolled_class_ids = set(my_enrs.mapped('class_id.id'))
            enrolled_classes = [e.class_id for e in my_enrs if e.class_id]

        # Find open classes
        classes = request.env['vus.class'].sudo().search([('state', '=', 'opened')])
        class_list = []
        today = fields.Date.today()
        for cls in classes:
            is_enrolled = (cls.id in enrolled_class_ids)

            # Check schedule conflict using standard overlap algorithm
            is_conflict = False
            conflict_reason = ''
            cls_sched = self._get_class_schedule(cls)
            if not is_enrolled and enrolled_classes:
                for enr_cls in enrolled_classes:
                    has_conflict, reason = check_classes_overlap(cls, enr_cls)
                    if has_conflict:
                        is_conflict = True
                        conflict_reason = reason
                        break

            # 1. Filter out if past closing date (registration deadline)
            if hasattr(cls, 'closing_date') and cls.closing_date and today > cls.closing_date:
                continue

            # 2. Filter out if more than 3 sessions completed
            completed_sheets = request.env['vus.attendance.sheet'].sudo().search_count([
                ('class_id', '=', cls.id),
                ('state', '=', 'done')
            ])
            if completed_sheets > 3:
                continue

            # check available seats
            current_count = len(cls.enrollment_ids.filtered(lambda e: e.state in ['confirmed', 'paid']))
            available_seats = cls.max_students - current_count

            class_list.append({
                'id': cls.id,
                'class_code': cls.class_code,
                'class_name': cls.class_name,
                'course_name': cls.course_id.course_name,
                'course_id': cls.course_id.id,
                'teacher_name': cls.teacher_id.name if cls.teacher_id else 'Chưa phân công',
                'schedule': cls_sched,
                'start_date': str(cls.start_date) if cls.start_date else '',
                'end_date': str(cls.end_date) if cls.end_date else '',
                'classroom': cls.classroom or '',
                'max_students': cls.max_students,
                'current_student_count': current_count,
                'available_seats': max(0, available_seats),
                'price': cls.course_id.base_price if cls.course_id else 0.0,
                'is_enrolled': is_enrolled,
                'is_conflict': is_conflict,
                'conflict_reason': conflict_reason
            })
        return self._json_response({'status': 'success', 'classes': class_list})

    def _get_class_target_dows(self, cls):
        """Get set of python weekdays (0=Mon, 1=Tue, ..., 6=Sun) for a class."""
        if not cls:
            return {0, 2, 4}

        if hasattr(cls, 'time_slot_id') and cls.time_slot_id and cls.time_slot_id.days_group:
            dg = cls.time_slot_id.days_group
            if dg == 'mwf':
                return {0, 2, 4}
            elif dg == 'tts':
                return {1, 3, 5}
            elif dg == 'ss':
                return {5, 6}

        sched_str = self._get_class_schedule(cls).lower()
        import re
        clean_text = re.sub(r'\d{1,2}[:.]\d{2}', '', sched_str)
        clean_text = re.sub(r'ca\s*\d', '', clean_text)

        target_dows = set()
        if 'thứ 2' in clean_text or 't2' in clean_text:
            target_dows.add(0)
        if 'thứ 3' in clean_text or 't3' in clean_text:
            target_dows.add(1)
        if 'thứ 4' in clean_text or 't4' in clean_text:
            target_dows.add(2)
        if 'thứ 5' in clean_text or 't5' in clean_text:
            target_dows.add(3)
        if 'thứ 6' in clean_text or 't6' in clean_text:
            target_dows.add(4)
        if 'thứ 7' in clean_text or 't7' in clean_text:
            target_dows.add(5)
        if 'chủ nhật' in clean_text or 'cn' in clean_text or 'thứ 8' in clean_text or 't8' in clean_text:
            target_dows.add(6)

        if not target_dows:
            target_dows = {0, 2, 4}

        return target_dows

    @http.route('/student/api/schedule', type='http', auth='public', methods=['GET'], csrf=False)
    def api_schedule(self, **kwargs):
        """Get student's class schedule events based on real vus.class.session and vus.attendance records."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        enrollments = request.env['vus.enrollment'].sudo().search([
            ('student_id', '=', student.id),
            ('state', 'in', ['confirmed', 'paid'])
        ])

        enrolled_class_ids = set(enrollments.mapped('class_id.id'))
        enrollment_map = {enr.class_id.id: enr.name for enr in enrollments if enr.class_id}

        events = []
        today = fields.Date.today()

        # Query all attendance records for this student
        attendances = request.env['vus.attendance'].sudo().search([
            ('student_id', '=', student.id)
        ])
        att_map = {}
        for att in attendances:
            if att.class_id and att.date:
                att_map[(att.class_id.id, str(att.date))] = att

        # 1. Query REAL vus.class.session records
        sessions = request.env['vus.class.session'].sudo().search([
            ('class_id', 'in', list(enrolled_class_ids))
        ], order='date asc')

        processed_session_dates = set()

        for sess in sessions:
            if not sess.class_id or not sess.date:
                continue
            date_str = str(sess.date)
            processed_session_dates.add((sess.class_id.id, date_str))

            # Check recorded attendance
            att = att_map.get((sess.class_id.id, date_str))
            if att:
                status = att.status
                status_label = dict(att._fields['status'].selection).get(att.status, att.status)
                color = '#10B981' if att.status == 'present' else ('#F59E0B' if att.status == 'late' else '#EF4444')
            else:
                if sess.date < today:
                    status = 'absent'
                    status_label = 'Vắng mặt'
                    color = '#EF4444'
                else:
                    status = 'upcoming'
                    status_label = 'Sắp diễn ra'
                    color = '#3B82F6'

            teacher_name = sess.teacher_id.name if sess.teacher_id else (sess.class_id.teacher_id.name if sess.class_id.teacher_id else 'Chưa phân công')

            events.append({
                'id': f"sess_{sess.id}",
                'class_id': sess.class_id.id,
                'class_code': sess.class_id.class_code,
                'class_name': sess.class_id.class_name,
                'course_name': sess.class_id.course_id.course_name if sess.class_id.course_id else '',
                'teacher_name': teacher_name,
                'classroom': sess.class_id.classroom or 'Chưa xếp phòng',
                'schedule': self._get_class_schedule(sess.class_id),
                'start_date': str(sess.class_id.start_date) if sess.class_id.start_date else '',
                'end_date': str(sess.class_id.end_date) if sess.class_id.end_date else '',
                'enrollment_code': enrollment_map.get(sess.class_id.id, ''),
                'title': f"{sess.class_id.class_name}",
                'session': f"Buổi {sess.session_number}",
                'session_number': sess.session_number,
                'date': date_str,
                'status': status,
                'status_label': status_label,
                'color': color,
                'type': 'session'
            })

        # 2. Fallback for classes that do NOT have vus.class.session generated yet
        for enr in enrollments:
            cls = enr.class_id
            if not cls or any(c_id == cls.id for (c_id, d) in processed_session_dates):
                continue

            target_dows = self._get_class_target_dows(cls)
            start = cls.start_date or today
            end = cls.end_date or (start + timedelta(days=90))
            cls_sched_text = self._get_class_schedule(cls)

            curr = start
            s_num = 1
            while curr <= end and s_num <= 36:
                if curr.weekday() in target_dows:
                    d_str = str(curr)
                    att = att_map.get((cls.id, d_str))
                    if att:
                        status = att.status
                        status_label = dict(att._fields['status'].selection).get(att.status, att.status)
                        color = '#10B981' if att.status == 'present' else ('#F59E0B' if att.status == 'late' else '#EF4444')
                    else:
                        if curr < today:
                            status = 'absent'
                            status_label = 'Vắng mặt'
                            color = '#EF4444'
                        else:
                            status = 'upcoming'
                            status_label = 'Sắp diễn ra'
                            color = '#3B82F6'

                    events.append({
                        'id': f"sched_{cls.id}_{d_str}",
                        'class_id': cls.id,
                        'class_code': cls.class_code,
                        'class_name': cls.class_name,
                        'course_name': cls.course_id.course_name if cls.course_id else '',
                        'teacher_name': cls.teacher_id.name if cls.teacher_id else 'Chưa phân công',
                        'classroom': cls.classroom or 'Chưa xếp phòng',
                        'schedule': cls_sched_text,
                        'start_date': str(cls.start_date) if cls.start_date else '',
                        'end_date': str(cls.end_date) if cls.end_date else '',
                        'enrollment_code': enr.name,
                        'title': f"{cls.class_name}",
                        'session': f"Buổi {s_num}",
                        'session_number': s_num,
                        'date': d_str,
                        'status': status,
                        'status_label': status_label,
                        'color': color,
                        'type': 'schedule'
                    })
                    s_num += 1
                curr += timedelta(days=1)

        return self._json_response({'status': 'success', 'schedule_events': events})

    @http.route('/student/api/campaigns', type='http', auth='public', methods=['GET'], csrf=False)
    def api_campaigns(self, **kwargs):
        """Get list of active marketing campaigns / programs for consultation selection."""
        campaigns = request.env['vus.marketing.campaign'].sudo().search([
            ('state', 'in', ['running', 'draft'])
        ], order='id desc')

        campaign_list = []
        for c in campaigns:
            campaign_list.append({
                'id': c.id,
                'name': c.name,
                'code': c.code,
                'start_date': str(c.start_date) if c.start_date else '',
                'end_date': str(c.end_date) if c.end_date else '',
                'description': c.description or ''
            })

        # Fallback to courses if no active campaign found
        if not campaign_list:
            courses = request.env['vus.course'].sudo().search([])
            for crs in courses:
                campaign_list.append({
                    'id': crs.id,
                    'name': f"Chương trình: {crs.course_name}",
                    'code': crs.code or 'COURSE'
                })

        return self._json_response({'status': 'success', 'campaigns': campaign_list})

    @http.route('/student/api/consult', type='http', auth='public', methods=['POST'], csrf=False)
    def api_consult(self, **kwargs):
        """Register consultation or placement test (Creates a CRM Lead linked to Marketing Campaign)."""
        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
            name = body.get('name', '').strip()
            phone = body.get('phone', '').strip()
            email = body.get('email', '').strip()
            campaign_id = body.get('campaign_id') or body.get('course_id')
            notes = body.get('notes', '').strip()
        except Exception:
            return self._json_response({'status': 'error', 'message': 'Dữ liệu đầu vào không hợp lệ!'}, status=400)

        if not name or not phone:
            return self._json_response({'status': 'error', 'message': 'Họ tên và Số điện thoại là bắt buộc!'}, status=400)

        # Check if logged in to link partner
        student = self._get_student()
        partner_id = student.id if student else False

        campaign_name = ''
        target_campaign_id = False

        if campaign_id:
            try:
                campaign = request.env['vus.marketing.campaign'].sudo().browse(int(campaign_id))
                if campaign.exists():
                    campaign_name = campaign.name
                    target_campaign_id = campaign.id
                else:
                    course = request.env['vus.course'].sudo().browse(int(campaign_id))
                    if course.exists():
                        campaign_name = course.course_name
            except Exception:
                pass

        description = f"Yêu cầu tư vấn từ Portal Học viên.\n"
        if campaign_name:
            description += f"Chương trình / Chiến dịch quan tâm: {campaign_name}\n"
        if notes:
            description += f"Lời nhắn của khách hàng: {notes}\n"

        lead_vals = {
            'name': f"Đăng ký tư vấn: {name} ({campaign_name or 'Chưa chọn chương trình'})",
            'contact_name': name,
            'phone': phone,
            'email_from': email or False,
            'description': description,
            'lead_source': 'web',
            'partner_id': partner_id
        }

        if target_campaign_id:
            lead_vals['vus_campaign_id'] = target_campaign_id

        # Create CRM Lead
        lead = request.env['crm.lead'].sudo().create(lead_vals)
        _logger.info("Created CRM Lead %s (Campaign: %s) from student portal registration.", lead.id, target_campaign_id)

        # Notify Managers in Odoo Systray
        note_html = (
            f'<p>📞 <b>YÊU CẦU TƯ VẤN MỚI TỪ PORTAL HỌC VIÊN</b></p>'
            f'<p>Khách hàng / Học viên <b>{name}</b> (SĐT: <b>{phone}</b>, Email: {email or "---"}) vừa gửi yêu cầu tư vấn.</p>'
            f'<p><b>Chương trình / Chiến dịch quan tâm:</b> <span style="color:#0C2B5C; font-weight:700;">{campaign_name or "Chưa chọn"}</span></p>'
            f'<p><b>Ghi chú:</b> {notes or "Không có"}</p>'
            f'<p>Vui lòng liên hệ hỗ trợ học viên trong thời gian sớm nhất.</p>'
        )
        self._create_manager_activities('crm.lead', lead.id, f"📞 Yêu cầu tư vấn [{campaign_name or 'Portal'}]: {name}", note_html)

        return self._json_response({
            'status': 'success',
            'campaign_name': campaign_name,
            'message': f'🎉 Đăng ký tư vấn thành công cho chương trình "{campaign_name or "VUS"}"! Bộ phận giáo vụ VUS sẽ liên hệ với bạn trong thời gian sớm nhất.'
        })

    @http.route('/student/api/enroll', type='http', auth='public', methods=['POST'], csrf=False)
    def api_enroll(self, **kwargs):
        """Register for a specific class (Creates a draft enrollment for the logged-in student)."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
            class_id = int(body.get('class_id'))
        except Exception:
            return self._json_response({'status': 'error', 'message': 'Vui lòng chọn lớp học!'}, status=400)

        cls = request.env['vus.class'].sudo().browse(class_id)
        if not cls.exists():
            return self._json_response({'status': 'error', 'message': 'Lớp học không tồn tại!'}, status=404)

        if cls.state != 'opened':
            return self._json_response({'status': 'error', 'message': 'Lớp học này hiện tại không mở đăng ký!'}, status=400)

        # Check seats
        current_count = len(cls.enrollment_ids.filtered(lambda e: e.state in ['confirmed', 'paid']))
        if current_count >= cls.max_students:
            return self._json_response({'status': 'error', 'message': 'Lớp học đã đạt sĩ số tối đa, vui lòng chọn lớp khác!'}, status=400)

        # Check if already enrolled in this class or course
        existing = request.env['vus.enrollment'].sudo().search([
            ('student_id', '=', student.id),
            ('class_id', '=', cls.id),
            ('state', 'in', ['draft', 'confirmed', 'paid'])
        ], limit=1)

        if existing:
            return self._json_response({'status': 'error', 'message': 'Bạn đã đăng ký lớp học này rồi!'})

        # Check schedule conflict with student's other active classes
        my_enrs = request.env['vus.enrollment'].sudo().search([
            ('student_id', '=', student.id),
            ('state', 'in', ['draft', 'confirmed', 'paid']),
            ('class_id', '!=', False)
        ])
        for enr in my_enrs:
            if enr.class_id and enr.class_id.id != cls.id:
                has_conflict, reason = check_classes_overlap(cls, enr.class_id)
                if has_conflict:
                    return self._json_response({
                        'status': 'error',
                        'message': f"⚠️ Không thể đăng ký lớp '{cls.class_name}' vì bị TRÙNG LỊCH HỌC với lớp '{enr.class_id.class_name}' mà bạn đã đăng ký!"
                    })

        # Create enrollment
        try:
            from odoo.exceptions import UserError, ValidationError
            enrollment = request.env['vus.enrollment'].sudo().create({
                'student_id': student.id,
                'course_id': cls.course_id.id,
                'class_id': cls.id,
                'enrollment_date': fields.Date.today(),
                'state': 'draft'
            })
            _logger.info("Student %s created draft enrollment %s for class %s", student.name, enrollment.name, cls.class_name)

            # Notify all Managers in Odoo Systray & Inbox directly on vus.enrollment
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
            enr_link = f"{base_url}/web#id={enrollment.id}&model=vus.enrollment&view_type=form"
            note_html = (
                f'<p>🚨 <b>ĐĂNG KÝ MỚI TỪ PORTAL HỌC VIÊN</b></p>'
                f'<p>Học viên <b>{student.name}</b> (Mã: {student.student_code or "---"}) vừa gửi đăng ký vào lớp <b>{cls.class_name}</b> ({cls.class_code}).</p>'
                f'<p>Mã phiếu ghi danh: <b>{enrollment.name}</b></p>'
                f'<p style="margin-top: 10px;">'
                f'  <a href="{enr_link}" target="_blank" style="background-color: #0C2B5C; color: #FFFFFF; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block;">'
                f'    👉 Click vào đây để mở và duyệt Phiếu {enrollment.name}'
                f'  </a>'
                f'</p>'
            )
            self._create_manager_activities('vus.enrollment', enrollment.id, f"🚨 Duyệt phiếu mới: {student.name}", note_html)

            return self._json_response({
                'status': 'success',
                'message': 'Đăng ký học thành công! Phiếu ghi danh nháp đã được tạo. Vui lòng kiểm tra mục thanh toán.',
                'enrollment': {
                    'id': enrollment.id,
                    'name': enrollment.name,
                    'amount': enrollment.amount
                }
            })
        except (UserError, ValidationError) as ve:
            msg = ve.args[0] if ve.args else str(ve)
            return self._json_response({'status': 'error', 'message': msg})
        except Exception as e:
            _logger.exception("Error creating enrollment from portal")
            return self._json_response({'status': 'error', 'message': f'Lỗi hệ thống khi đăng ký: {str(e)}'})

    @http.route('/student/api/invoices', type='http', auth='public', methods=['GET'], csrf=False)
    def api_invoices(self, **kwargs):
        """Get tuition invoices / payments for the logged-in student."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        enrollments = request.env['vus.enrollment'].sudo().search([('student_id', '=', student.id)], order='id desc')
        invoice_list = []
        for enr in enrollments:
            invoice_name = ''
            payment_state = 'Chưa tạo hóa đơn'
            payment_code = ''
            due_date_str = ''
            
            # Compute due date (payment deadline)
            if enr.invoice_id and enr.invoice_id.invoice_date_due:
                due_date_str = str(enr.invoice_id.invoice_date_due)
            elif enr.class_id and enr.class_id.start_date:
                due_date_str = str(enr.class_id.start_date)
            elif enr.enrollment_date:
                due_date_str = str(enr.enrollment_date + timedelta(days=7))

            if enr.state == 'cancel':
                payment_state = 'Đã hủy'
            elif enr.invoice_id:
                invoice_name = enr.invoice_id.name or ''
                raw_state = enr.invoice_id.payment_state
                if raw_state in ['paid', 'in_payment']:
                    payment_state = 'Đã thanh toán'
                elif enr.invoice_id.state == 'posted':
                    payment_state = 'Chờ thanh toán'
                else:
                    payment_state = 'Chưa xác nhận (Nháp)'
                payment_code = enr.invoice_id.payment_reference or enr.invoice_id.name
            else:
                if enr.state == 'draft':
                    payment_state = 'Chưa xác nhận (Nháp)'
                elif enr.state == 'confirmed':
                    payment_state = 'Chờ thanh toán'
                elif enr.state == 'paid':
                    payment_state = 'Đã thanh toán'

            invoice_list.append({
                'id': enr.id,
                'enrollment_code': enr.name,
                'course_name': enr.course_id.course_name if enr.course_id else '',
                'class_name': enr.class_id.class_name if enr.class_id else 'Chưa chọn lớp',
                'amount': enr.amount,
                'date': str(enr.enrollment_date),
                'due_date': due_date_str,
                'invoice_name': invoice_name,
                'payment_state': payment_state,
                'payment_code': payment_code or enr.name,
                'state': enr.state
            })
        return self._json_response({'status': 'success', 'invoices': invoice_list})

    @http.route('/student/api/attendance', type='http', auth='public', methods=['GET'], csrf=False)
    def api_attendance(self, **kwargs):
        """Get attendance records for the logged-in student."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        attendances = request.env['vus.attendance'].sudo().search([('student_id', '=', student.id)], order='date desc')
        attendance_list = []
        for att in attendances:
            status_label = dict(att._fields['status'].selection).get(att.status, att.status)
            attendance_list.append({
                'id': att.id,
                'class_name': att.class_id.class_name if att.class_id else '',
                'date': str(att.date),
                'session': att.session or '',
                'status': att.status,
                'status_label': status_label,
                'note': att.note or ''
            })
        return self._json_response({'status': 'success', 'attendance': attendance_list})

    @http.route('/student/api/enroll/cancel', type='http', auth='public', methods=['POST'], csrf=False)
    def api_enroll_cancel(self, **kwargs):
        """Cancel a draft enrollment before manager confirmation."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
            enrollment_id = int(body.get('enrollment_id'))
        except Exception:
            return self._json_response({'status': 'error', 'message': 'Dữ liệu không hợp lệ!'}, status=400)

        enrollment = request.env['vus.enrollment'].sudo().browse(enrollment_id)
        if not enrollment.exists() or enrollment.student_id.id != student.id:
            return self._json_response({'status': 'error', 'message': 'Không tìm thấy phiếu ghi danh!'}, status=404)

        # Allow cancel if: draft (chưa xác nhận) OR confirmed unpaid
        can_cancel = False
        if enrollment.state in ['draft', 'confirmed']:
            if not enrollment.invoice_id or enrollment.invoice_id.payment_state == 'not_paid':
                can_cancel = True

        if not can_cancel:
            return self._json_response({'status': 'error', 'message': 'Không thể hủy phiếu đã thanh toán hoặc đang xử lý!'}, status=400)

        try:
            enrollment_name = enrollment.name
            invoice = enrollment.invoice_id

            # Cancel linked invoice if it exists and is not paid
            if invoice and invoice.payment_state == 'not_paid':
                try:
                    if invoice.state == 'posted':
                        invoice.button_cancel()
                    invoice.unlink()
                    _logger.info("Cancelled and deleted invoice %s for enrollment %s", invoice.name, enrollment_name)
                except Exception as inv_err:
                    _logger.warning("Could not delete invoice %s: %s", invoice.name if invoice else '?', str(inv_err))

            # Set state to 'cancel'
            enrollment.write({'state': 'cancel'})

            # Also cancel/unlink any manager activities on student partner for this enrollment
            try:
                activities = request.env['mail.activity'].sudo().search([
                    ('res_model', '=', 'res.partner'),
                    ('res_id', '=', student.id),
                    ('summary', 'like', 'Duyệt đăng ký học%')
                ])
                for act in activities:
                    if enrollment_name in (act.note or ''):
                        act.unlink()
            except Exception as act_err:
                _logger.error("Failed to delete related manager activities: %s", str(act_err))

            _logger.info("Student %s cancelled enrollment %s", student.name, enrollment_name)
            return self._json_response({'status': 'success', 'message': 'Đã hủy đăng ký lớp học thành công.'})
        except Exception as e:
            _logger.error("Cancel enrollment error: %s", str(e))
            return self._json_response({'status': 'error', 'message': f'Lỗi khi hủy đăng ký: {str(e)}'}, status=500)

    @http.route('/student/api/vnpay/pay', type='http', auth='public', methods=['POST'], csrf=False)
    def api_vnpay_pay(self, **kwargs):
        """Generate VNPay Payment Gateway URL for a selected enrollment."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
            enrollment_id = int(body.get('enrollment_id'))
        except Exception:
            return self._json_response({'status': 'error', 'message': 'Dữ liệu không hợp lệ!'}, status=400)

        enrollment = request.env['vus.enrollment'].sudo().browse(enrollment_id)
        if not enrollment.exists() or enrollment.student_id.id != student.id:
            return self._json_response({'status': 'error', 'message': 'Không tìm thấy phiếu ghi danh!'}, status=404)

        amount_int = int(enrollment.amount * 100)
        vnp_url = f"https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_Amount={amount_int}&vnp_Command=pay&vnp_CreateDate={fields.Datetime.now().strftime('%Y%m%d%H%M%S')}&vnp_CurrCode=VND&vnp_IpAddr=127.0.0.1&vnp_Locale=vn&vnp_OrderInfo=VUS+PAY+{enrollment.name}&vnp_OrderType=billpayment&vnp_TxnRef={enrollment.name}&vnp_Version=2.1.0"

        return self._json_response({
            'status': 'success',
            'payment_url': vnp_url,
            'enrollment_code': enrollment.name,
            'amount': enrollment.amount,
            'message': f'Đã tạo cổng thanh toán VNPay cho phiếu {enrollment.name}'
        })

    @http.route('/student/api/vnpay/simulate', type='http', auth='public', methods=['POST'], csrf=False)
    def api_vnpay_simulate(self, **kwargs):
        """Simulate successful VNPay payment demo in Odoo."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
            enrollment_id = int(body.get('enrollment_id'))
        except Exception:
            return self._json_response({'status': 'error', 'message': 'Dữ liệu không hợp lệ!'}, status=400)

        enrollment = request.env['vus.enrollment'].sudo().browse(enrollment_id)
        if not enrollment.exists() or enrollment.student_id.id != student.id:
            return self._json_response({'status': 'error', 'message': 'Không tìm thấy phiếu ghi danh!'}, status=404)

        try:
            # Mark enrollment as paid
            enrollment.sudo().write({'state': 'paid'})
            
            # Mark invoice as paid if linked
            if enrollment.invoice_id:
                enrollment.invoice_id.sudo().write({'payment_state': 'paid'})

            # Mark partner as student
            if student:
                student.sudo().write({'is_student': True})

            _logger.info("Demo VNPay payment completed for enrollment %s student %s", enrollment.name, student.name)
            return self._json_response({
                'status': 'success',
                'message': f'🎉 Thanh toán Demo thành công số tiền {enrollment.amount:,.0f} đ cho phiếu {enrollment.name}! Trạng thái đã chuyển sang Đã thanh toán.'
            })
        except Exception as e:
            _logger.error("Simulate payment error: %s", str(e))
            return self._json_response({'status': 'error', 'message': f'Lỗi khi xử lý thanh toán demo: {str(e)}'}, status=500)



    @http.route('/student/api/my-classes', type='http', auth='public', methods=['GET'], csrf=False)
    def api_my_classes(self, **kwargs):
        """Get list of classes that the logged-in student is currently enrolled in."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        # Search for confirmed or paid enrollments for this student
        enrollments = request.env['vus.enrollment'].sudo().search([
            ('student_id', '=', student.id),
            ('state', 'in', ['confirmed', 'paid'])
        ])

        classes_list = []
        for enr in enrollments:
            cls = enr.class_id
            if not cls:
                continue
            
            # format schedule string
            schedule_str = self._get_class_schedule(cls)

            # Calculate attendance rate for this specific class
            attendances = request.env['vus.attendance'].sudo().search([
                ('student_id', '=', student.id),
                ('class_id', '=', cls.id)
            ], order='date asc')
            att_total = len(attendances)
            att_present = sum(1 for a in attendances if a.status in ['present', 'late'])
            att_rate = round((att_present / att_total) * 100) if att_total > 0 else 100

            classes_list.append({
                'id': cls.id,
                'enrollment_id': enr.id,
                'enrollment_code': enr.name,
                'class_code': cls.class_code,
                'class_name': cls.class_name,
                'course_name': cls.course_id.course_name,
                'teacher_name': cls.teacher_id.name if cls.teacher_id else 'Chưa phân công',
                'schedule': schedule_str,
                'start_date': str(cls.start_date) if cls.start_date else '',
                'end_date': str(cls.end_date) if cls.end_date else '',
                'classroom': cls.classroom or '',
                'enrollment_state': 'Đang học' if enr.state == 'paid' else 'Chờ đóng phí',
                'attendance_rate': f"{att_rate}%",
                'attendance_total': att_total,
                'attendance_present': att_present,
            })
        return self._json_response({'status': 'success', 'my_classes': classes_list})

    @http.route('/student/api/class-attendance', type='http', auth='public', methods=['GET'], csrf=False)
    def api_class_attendance(self, class_id=None, **kwargs):
        """Get detailed attendance records for a specific class for the logged-in student."""
        student = self._get_student()
        if not student:
            return self._json_response({'status': 'error', 'message': 'Chưa đăng nhập!'}, status=401)

        if not class_id:
            return self._json_response({'status': 'error', 'message': 'Thiếu class_id!'}, status=400)

        try:
            class_id = int(class_id)
        except (ValueError, TypeError):
            return self._json_response({'status': 'error', 'message': 'class_id không hợp lệ!'}, status=400)

        attendances = request.env['vus.attendance'].sudo().search([
            ('student_id', '=', student.id),
            ('class_id', '=', class_id)
        ], order='date asc')

        att_list = []
        for att in attendances:
            status_label = dict(att._fields['status'].selection).get(att.status, att.status)
            att_list.append({
                'id': att.id,
                'date': str(att.date),
                'session': att.session or '',
                'status': att.status,
                'status_label': status_label,
                'note': att.note or ''
            })

        return self._json_response({'status': 'success', 'attendance': att_list})

