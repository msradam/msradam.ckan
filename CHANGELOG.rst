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

- ckan_dataset - manage datasets (packages) on a CKAN portal
- ckan_dataset_info - fetch information about a dataset
- ckan_dataset_search - search datasets with Solr query syntax
- ckan_group - manage thematic groups on a CKAN portal
- ckan_organization - manage organizations on a CKAN portal
- ckan_organization_info - fetch information about an organization
- ckan_organization_member - manage user membership and roles in an organization
- ckan_status_info - fetch site status and CKAN version
- ckan_user - manage users on a CKAN portal
- ckan_user_info - fetch information about a user

New Modules
-----------

- ckan_dataset - Manage CKAN datasets
- ckan_dataset_info - Retrieve information about a CKAN dataset
- ckan_dataset_search - Search datasets on a CKAN portal
- ckan_group - Manage CKAN groups
- ckan_organization - Manage CKAN organizations
- ckan_organization_info - Retrieve information about a CKAN organization
- ckan_organization_member - Manage user membership in a CKAN organization
- ckan_status_info - Retrieve status and version information from a CKAN portal
- ckan_user - Manage CKAN users
- ckan_user_info - Retrieve information about a CKAN user
