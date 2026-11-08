
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from exams.models import Exam


def student_login(request):
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=roll_number,
            password=password
        )

        if user is not None and user.role == 'STUDENT':
            login(request, user)
            return redirect('student_dashboard')
        else:
            messages.error(
                request,
                'Invalid Roll Number or Password'
            )

    return render(request, 'accounts/student_login.html')


@login_required
def student_dashboard(request):
    if request.user.role != 'STUDENT':
        return redirect('student_login')

    return render(
        request,
        'accounts/student_dashboard.html'
    )


@login_required
def exam_verification(request):
    if request.user.role != 'STUDENT':
        return redirect('student_login')

    if request.method == 'POST':
        code = request.POST.get(
            'verification_code', ''
        ).strip()

        exam = Exam.objects.filter(
            verification_code=code,
            is_active=True
        ).first()

        if exam:
            request.session['verified_exam_id'] = exam.id
            return redirect('exam_instructions')
        else:
            messages.error(
                request,
                'Invalid code or examination is not active.'
            )

    return render(
        request,
        'accounts/exam_verification.html'
    )


@login_required
def exam_instructions(request):
    if request.user.role != 'STUDENT':
        return redirect('student_login')

    exam_id = request.session.get('verified_exam_id')

    if not exam_id:
        return redirect('exam_verification')

    exam = Exam.objects.filter(
        id=exam_id,
        is_active=True
    ).first()

    if not exam:
        request.session.pop('verified_exam_id', None)
        messages.error(
            request,
            'This examination is unavailable.'
        )
        return redirect('student_dashboard')

    return render(
        request,
        'accounts/exam_instructions.html',
        {'exam': exam}
    )
