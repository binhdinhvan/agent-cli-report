"""OpenAI short-context cache accounting; pure offline functions, no credential/network IO."""
from decimal import Decimal, InvalidOperation


REVISION = 'openai-cache-cost-r2'


def estimate(usage, pricing):
    """Use exact lifetime counts when present; otherwise bound unknown writes at12h rate.

    All input categories are disjoint. Unknown usage remains unknown, never zero.
    The fallback is a documented conservative tariff estimate, NOT an invoice estimate.
    """
    answer = {'revision': REVISION, 'usage': usage, 'estimated_cost_usd': None,
              'measured_charge_usd': None, 'estimate_status': 'unpriced'}

    def reject(reason):
        answer['reason'] = reason
        return answer

    if not isinstance(usage, dict) or not isinstance(usage.get('input_tokens_details'), dict):
        return reject('Missing usage/input details; not replaced with zero')
    details = usage['input_tokens_details']
    values = [usage.get('input_tokens'), usage.get('output_tokens'),
              details.get('cached_tokens'), details.get('cache_write_tokens')]
    if not all(type(n) is int and n >= 0 for n in values):
        return reject('Missing/non-integer/negative input/output/cache counts')
    incoming, outgoing, cached, written = values
    if incoming > 272000:
        return reject('Long-context tariff not approved')
    ordinary = incoming - cached - written
    if ordinary < 0:
        return reject('Cached reads plus writes exceed total input')
    if 'total_tokens' in usage and (type(usage['total_tokens']) is not int
                                    or usage['total_tokens'] != incoming + outgoing):
        return reject('Invalid total token accounting')
    output_details = usage.get('output_tokens_details')
    if output_details is not None:
        if not isinstance(output_details, dict):
            return reject('Invalid output token details')
        if 'reasoning_tokens' in output_details:
            reasoning = output_details['reasoning_tokens']
            if type(reasoning) is not int or not 0 <= reasoning <= outgoing:
                return reject('Invalid reasoning token accounting')
    breakdown = details.get('cache_write_tokens_details')
    bounded = False
    if 'cache_write_tokens_details' in details:
        if not isinstance(breakdown, dict):
            return reject('Invalid cache-write lifetime details')
        short, long = breakdown.get('ttl_30m_tokens'), breakdown.get('ttl_12h_tokens')
        if not all(type(n) is int and n >= 0 for n in (short, long)) or short + long != written:
            return reject('Cache-write lifetime counts must sum to writes')
    elif written:
        # No guess about requested TTL, server default, or an individual breakpoint.
        short, long, bounded = 0, written, True
    else:
        short, long = 0, 0
    try:
        unit = Decimal(pricing['unit_tokens'])
        names = ('input_uncached', 'input_cache_read', 'cache_write_30m', 'cache_write_12h', 'output')
        rates = {name: Decimal(pricing[name]) for name in names}
        if not unit.is_finite() or unit <= 0 or any(not r.is_finite() or r < 0 for r in rates.values()):
            return reject('Invalid pricing')
        if rates['cache_write_12h'] < rates['cache_write_30m']:
            return reject('12h tariff must bound30m tariff for conservative fallback')
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return reject('Missing/invalid OpenAI cache pricing')
    components = {
        'ordinary_input_usd': Decimal(ordinary) * rates['input_uncached'] / unit,
        'cached_input_usd': Decimal(cached) * rates['input_cache_read'] / unit,
        'cache_write_30m_usd': Decimal(short) * rates['cache_write_30m'] / unit,
        'cache_write_12h_usd': Decimal(long) * rates['cache_write_12h'] / unit,
        'output_usd': Decimal(outgoing) * rates['output'] / unit,
    }
    lower = (Decimal(ordinary) * rates['input_uncached'] + Decimal(cached) * rates['input_cache_read']
             + Decimal(written) * rates['cache_write_30m'] + Decimal(outgoing) * rates['output']) / unit
    total = sum(components.values())
    answer.update(estimated_cost_usd=format(total, 'f'),
        components={k: format(v, 'f') for k, v in components.items()},
        ordinary_input_tokens=ordinary, cached_input_tokens=cached, cache_write_tokens=written,
        billed_30m_write_tokens=None if bounded else short,
        billed_12h_write_tokens=None if bounded else long,
        guard_30m_write_tokens=short, guard_12h_write_tokens=long,
        cache_write_lifetime_status='unknown_bounded_at_12h_rate' if bounded else 'reported_breakdown_or_zero_writes',
        conservative_upper_bound=bounded,
        published_tariff_lower_usd=format(lower if bounded else total, 'f'),
        published_tariff_upper_usd=format(total, 'f'),
        estimate_status=('conservative published-tariff upper estimate; unknown write lifetime charged at12h guard rate'
                         if bounded else 'published OpenAI tariff estimate from reported lifetime counts'),
        limitations='not invoice-confirmed; not an invoice cap; excludes unreported fees; reasoning included in output, not added again')
    return answer
