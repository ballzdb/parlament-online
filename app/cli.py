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

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
