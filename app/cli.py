from __future__ import annotations

import argparse
import os
import sys

import django


def main():
    parser = argparse.ArgumentParser(description='Parlament.Online CLI')
    subparsers = parser.add_subparsers(dest='command')

    create_secretary = subparsers.add_parser('create-secretary', help='Create the first secretary account')
    create_secretary.add_argument('--email', default='secretary@parlament-online.local')
    create_secretary.add_argument('--password', default='Parlament123!')
    create_secretary.add_argument('--name', default='Секретар')

    args = parser.parse_args()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    if args.command == 'create-secretary':
        from django.core.management import call_command
        call_command('create_secretary', email=args.email, password=args.password, name=args.name)
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
