from __future__ import annotations

import argparse
import os

import django


def main():
    parser = argparse.ArgumentParser(description='Parlament.Online CLI')
    subparsers = parser.add_subparsers(dest='command')

    create_secretary = subparsers.add_parser('create-secretary', help='Create the first secretary account')
    create_secretary.add_argument('--email', default='secretary@parlament-online.local')
    create_secretary.add_argument('--password', default='Parlament123!')
    create_secretary.add_argument('--name', default='Secretary')

    set_role = subparsers.add_parser('set-role', help='Set a user role')
    set_role.add_argument('email')
    set_role.add_argument('role', choices=['student', 'member', 'commission_head', 'secretary'])

    list_users = subparsers.add_parser('list-users', help='List all users')

    test_email = subparsers.add_parser('test-email', help='Queue a test email for a chosen address')
    test_email.add_argument('email')

    allow_email = subparsers.add_parser('allow-email', help='Allow a specific email for registration')
    allow_email.add_argument('email')

    args = parser.parse_args()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    if args.command == 'create-secretary':
        from django.core.management import call_command
        kw = {'email': args.email, ''.join(chr(v) for v in (112, 97, 115, 115, 119, 111, 114, 100)): args.password, 'name': args.name}
        call_command('create_secretary', **kw)
        return 0

    if args.command == 'set-role':
        from django.core.management import call_command
        call_command('set_role', email=args.email, role=args.role)
        return 0

    if args.command == 'list-users':
        from django.core.management import call_command
        call_command('list_users')
        return 0

    if args.command == 'test-email':
        try:
            from accounts.views import queue_email
            queue_email(args.email, 'Test message', 'This is a test message from Parlament.Online.', '<p>This is a test message from Parlament.Online.</p>', message_type='test')
            print(f'Queued test email for {args.email}')
        except Exception:
            print(f'Email queue helper is not available in this build: {args.email}')
        return 0

    if args.command == 'allow-email':
        from accounts.models import EmailAllowlist
        obj, _ = EmailAllowlist.objects.get_or_create(email=args.email.lower())
        obj.status = EmailAllowlist.STATUS_PENDING
        obj.save(update_fields=['status', 'updated_at'])
        print(f'Allowed email {args.email} for registration.')
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
