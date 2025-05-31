#!/usr/bin/env python3
"""
AWS SSO Enabled Users and Permissions Fetcher

This script retrieves only enabled AWS SSO (IAM Identity Center) users, their assigned
permission sets, and account access information.

Requirements:
- AWS CLI configured or appropriate environment variables set
- boto3 library installed (pip install boto3)
- Appropriate AWS permissions to access IAM Identity Center information
"""

import boto3
import json
import time
from botocore.exceptions import ClientError
from datetime import datetime


def get_identity_store_client(profile_name=None, region_name=None):
    """Create and return an AWS Identity Store client."""
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    return session.client('identitystore')


def get_sso_admin_client(profile_name=None, region_name=None):
    """Create and return an AWS SSO Admin client."""
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    return session.client('sso-admin')


def get_organizations_client(profile_name=None, region_name=None):
    """Create and return an AWS Organizations client."""
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    return session.client('organizations')


def get_instance_info(sso_admin_client):
    """Get the SSO instance ARN and Identity Store ID."""
    try:
        response = sso_admin_client.list_instances()
        if response['Instances']:
            instance = response['Instances'][0]
            return instance['InstanceArn'], instance['IdentityStoreId']
        else:
            print("No SSO instances found")
            return None, None
    except ClientError as e:
        print(f"Error getting SSO instance: {e}")
        return None, None


def get_account_assignments_for_user(sso_admin_client, instance_arn, permission_sets, user_id):
    """Get all assignments for a specific user across all permission sets and accounts."""
    all_assignments = []

    for ps_arn in permission_sets:
        # Get accounts for this permission set
        try:
            accounts = []
            paginator = sso_admin_client.get_paginator('list_accounts_for_provisioned_permission_set')

            for page in paginator.paginate(
                    InstanceArn=instance_arn,
                    PermissionSetArn=ps_arn
            ):
                accounts.extend(page['AccountIds'])

            # For each account, check if this user has an assignment
            for account_id in accounts:
                try:
                    paginator = sso_admin_client.get_paginator('list_account_assignments')

                    for page in paginator.paginate(
                            InstanceArn=instance_arn,
                            AccountId=account_id,
                            PermissionSetArn=ps_arn
                    ):
                        # Filter assignments for this user
                        user_assignments = [a for a in page['AccountAssignments']
                                            if a['PrincipalType'] == 'USER' and a['PrincipalId'] == user_id]

                        if user_assignments:
                            for assignment in user_assignments:
                                assignment['PermissionSetArn'] = ps_arn
                                assignment['AccountId'] = account_id
                                all_assignments.append(assignment)

                except ClientError as e:
                    print(f"Error getting account assignments for user {user_id} in account {account_id}: {e}")
                    continue

        except ClientError as e:
            print(f"Error getting accounts for permission set {ps_arn}: {e}")
            continue

    return all_assignments


def get_all_permission_sets(sso_admin_client, instance_arn):
    """Get all permission sets in the SSO instance."""
    try:
        permission_sets = []
        paginator = sso_admin_client.get_paginator('list_permission_sets')

        for page in paginator.paginate(InstanceArn=instance_arn):
            permission_sets.extend(page['PermissionSets'])

        return permission_sets
    except ClientError as e:
        print(f"Error getting permission sets: {e}")
        return []


def get_permission_set_details(sso_admin_client, instance_arn, permission_set_arn):
    """Get details for a specific permission set."""
    try:
        response = sso_admin_client.describe_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        ps_details = response['PermissionSet']

        # Get managed policies
        try:
            policies_response = sso_admin_client.list_managed_policies_in_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn
            )
            ps_details['ManagedPolicies'] = policies_response.get('AttachedManagedPolicies', [])
        except ClientError:
            ps_details['ManagedPolicies'] = []

        # Get inline policy
        try:
            inline_policy_response = sso_admin_client.get_inline_policy_for_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn
            )
            ps_details['InlinePolicy'] = inline_policy_response.get('InlinePolicy', '')
        except ClientError:
            ps_details['InlinePolicy'] = ''

        return ps_details
    except ClientError as e:
        print(f"Error getting permission set details for {permission_set_arn}: {e}")
        return {}


def get_account_name(organizations_client, account_id):
    """Get the name of an AWS account by its ID."""
    try:
        response = organizations_client.describe_account(AccountId=account_id)
        return response['Account']['Name']
    except ClientError as e:
        print(f"Error getting account name for {account_id}: {e}")
        return account_id  # Return the account ID if name can't be retrieved


def export_to_json(data, filename):
    """Export data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Data exported to {filename}")


def main():
    print("AWS SSO (IAM Identity Center) Enabled Users and Permissions Fetcher")
    print("----------------------------------------------------------------")

    profile_name = input("Enter AWS profile name (leave blank for default credentials): ").strip() or None
    region_name = input("Enter AWS region (leave blank for us-east-1): ").strip() or 'us-east-1'

    print(f"\nConnecting to AWS using {'default' if profile_name is None else profile_name} profile...")

    # Initialize clients
    sso_admin_client = get_sso_admin_client(profile_name, region_name)
    identity_store_client = get_identity_store_client(profile_name, region_name)
    organizations_client = get_organizations_client(profile_name, region_name)

    # Get SSO instance and identity store IDs
    instance_arn, identity_store_id = get_instance_info(sso_admin_client)
    if not instance_arn or not identity_store_id:
        print("Failed to get SSO instance information. Exiting.")
        return

    # Get all permission sets
    print("Fetching permission sets...")
    permission_sets = get_all_permission_sets(sso_admin_client, instance_arn)
    permission_set_details = {}
    for ps_arn in permission_sets:
        permission_set_details[ps_arn] = get_permission_set_details(sso_admin_client, instance_arn, ps_arn)
    print(f"Found {len(permission_sets)} permission sets")

    # Get all users first
    print("Fetching all SSO users...")
    all_users = []
    try:
        paginator = identity_store_client.get_paginator('list_users')
        for page in paginator.paginate(IdentityStoreId=identity_store_id):
            all_users.extend(page['Users'])
    except ClientError as e:
        print(f"Error fetching users: {e}")
        return

    print(f"Found {len(all_users)} total users")

    # Now collect only users with active assignments - these are enabled users
    enabled_users = []
    for user in all_users:
        user_id = user['UserId']
        user_name = user.get('UserName', user_id)

        print(f"Checking if user {user_name} has active assignments...")

        # Get assignments for this user
        assignments = get_account_assignments_for_user(
            sso_admin_client, instance_arn, permission_sets, user_id
        )

        # If user has assignments, they are considered active/enabled
        if assignments:
            print(f"User {user_name} has {len(assignments)} assignments - considered ENABLED")

            # Enrich with email if available
            email = ""
            for attr in user.get('Emails', []):
                if attr.get('Primary', False):
                    email = attr.get('Value', '')
                    break

            # Process each assignment
            processed_assignments = []
            for assignment in assignments:
                account_id = assignment['AccountId']
                ps_arn = assignment['PermissionSetArn']

                # Get account name
                account_name = get_account_name(organizations_client, account_id)

                # Get permission set details
                ps_name = permission_set_details[ps_arn].get('Name', '')
                ps_policies = permission_set_details[ps_arn].get('ManagedPolicies', [])

                processed_assignments.append({
                    'AccountId': account_id,
                    'AccountName': account_name,
                    'PermissionSetArn': ps_arn,
                    'PermissionSetName': ps_name,
                    'ManagedPolicies': ps_policies
                })

            # Add user to enabled users list
            enabled_users.append({
                'UserId': user_id,
                'UserName': user_name,
                'Email': email,
                'Status': 'ENABLED',
                'Assignments': processed_assignments
            })
        else:
            print(f"User {user_name} has no assignments - DISABLED or INACTIVE")

    # Export data - only JSON file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f"aws_sso_enabled_users_{timestamp}.json"
    export_to_json(enabled_users, json_filename)

    print("\nSummary:")
    print(f"Total users in SSO: {len(all_users)}")
    print(f"Total enabled users (with assignments): {len(enabled_users)}")
    print(f"Total permission sets: {len(permission_sets)}")
    print(f"Data exported to {json_filename}")


if __name__ == "__main__":
    main()
