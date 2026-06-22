=====================================
msradam.ckan Collection Release Notes
=====================================

.. contents:: Topics

v0.1.0
======

Release Summary
---------------

Initial release of the msradam.ckan Ansible collection.
Provides idempotent modules for managing CKAN open-data portal resources
via the CKAN Action API. Validated against CKAN 2.11.5.

Minor Changes
-------------

- ckan_api_token - create and revoke API tokens for a CKAN user
- ckan_dataset - manage datasets (packages) on a CKAN portal
- ckan_dataset_info - fetch a single dataset by name or id
- ckan_dataset_search - search datasets with Solr query syntax
- ckan_group - manage thematic groups on a CKAN portal
- ckan_group_member - manage user membership and roles in a group
- ckan_organization - manage organizations on a CKAN portal
- ckan_organization_info - fetch a single organization by name or id
- ckan_organization_member - manage user membership and roles in an organization
- ckan_resource - manage URL resources attached to a dataset
- ckan_resource_info - fetch a single resource by UUID
- ckan_status_info - fetch site status and CKAN version
- ckan_user - manage users on a CKAN portal
- ckan_user_info - fetch a single user by name or id

New Modules
-----------

- ckan_api_token - Manage CKAN API tokens for a user
- ckan_dataset - Manage CKAN datasets
- ckan_dataset_info - Retrieve information about a CKAN dataset
- ckan_dataset_search - Search datasets on a CKAN portal
- ckan_group - Manage CKAN groups
- ckan_group_member - Manage user membership in a CKAN group
- ckan_organization - Manage CKAN organizations
- ckan_organization_info - Retrieve information about a CKAN organization
- ckan_organization_member - Manage user membership in a CKAN organization
- ckan_resource - Manage resources attached to a CKAN dataset
- ckan_resource_info - Retrieve information about a CKAN resource
- ckan_status_info - Retrieve status and version information from a CKAN portal
- ckan_user - Manage CKAN users
- ckan_user_info - Retrieve information about a CKAN user
