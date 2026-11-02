"""Shared WP arguments, aligned with the imported original spectool runner."""
import os

def verification_profile():
    profile=os.environ.get('ACSL_FRAMAC_PROFILE','original').strip().lower()
    if profile not in ('original','strict'):
        raise ValueError('ACSL_FRAMAC_PROFILE must be original or strict')
    return profile

def wp_arguments(timeout):
    args=['-wp','-wp-precond-weakening']
    if verification_profile()=='original':
        args+=['-wp-no-callee-precond']
    else:
        args+=['-wp-rte']
    return args+['-wp-prover','Alt-Ergo,Z3','-wp-print','-wp-timeout',str(max(1,int(timeout)))]

def profile_metadata():
    profile=verification_profile()
    return {'verification_profile':profile,'rte_checks':profile=='strict','callee_precondition_checks':profile=='strict'}
