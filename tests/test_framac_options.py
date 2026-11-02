from engine.verification.framac_options import wp_arguments,profile_metadata
from engine.verification.framac_runtime import _frama_c_args
from pathlib import Path

def test_original_command_matches_original_spectool(monkeypatch):
 monkeypatch.delenv('ACSL_FRAMAC_PROFILE',raising=False)
 expected=['-wp','-wp-precond-weakening','-wp-no-callee-precond','-wp-prover','Alt-Ergo,Z3','-wp-print','-wp-timeout','15']
 assert wp_arguments(15)==expected
 assert _frama_c_args([Path('case.c')],15,None,'single')==['frama-c',*expected,'case.c']
 assert profile_metadata()=={'verification_profile':'original','rte_checks':False,'callee_precondition_checks':False}

def test_strict_profile_is_explicit(monkeypatch):
 monkeypatch.setenv('ACSL_FRAMAC_PROFILE','strict')
 args=wp_arguments(8)
 assert '-wp-rte' in args and '-wp-no-callee-precond' not in args
 assert profile_metadata()['rte_checks'] is True
