def landing_page_context(request):
    """
    Context processor for the landing page content.
    This makes the landing page content dynamic and easily editable.
    """
    return {
        'landing_page': {
            'hero': {
                'title': 'Transform Your Agricultural Education Journey',
                'description': 'TAU Agrostudies Portal connects students with world-class agricultural training opportunities and farm placements to develop the next generation of agricultural leaders.',
                'stats': [
                    {'number': '100+', 'label': 'Partner Farms'},
                    {'number': '1,000+', 'label': 'Students Placed'},
                    {'number': '95%', 'label': 'Completion Rate'},
                ]
            },
            'features': {
                'title': 'Comprehensive Agricultural Training',
                'description': 'Our program offers a complete ecosystem for agricultural education and practical experience',
                'items': [
                    {
                        'icon': 'bi-book',
                        'title': 'Specialized Curriculum',
                        'description': 'Access to specialized agricultural courses designed by industry experts and academics.'
                    },
                    {
                        'icon': 'bi-house',
                        'title': 'Farm Placements',
                        'description': 'Hands-on experience at leading agricultural operations across the country.'
                    },
                    {
                        'icon': 'bi-people',
                        'title': 'Mentorship Program',
                        'description': 'One-on-one guidance from experienced agricultural professionals throughout your journey.'
                    },
                    {
                        'icon': 'bi-graph-up',
                        'title': 'Career Development',
                        'description': 'Job placement assistance and entrepreneurship opportunities after program completion.'
                    }
                ]
            },
            'benefits': {
                'title': 'Why Choose TAU Agrostudies?',
                'description': 'Our program is designed to provide comprehensive agricultural education with real-world experience',
                'items': [
                    {
                        'icon': 'bi-award',
                        'title': 'Internationally Recognized',
                        'description': 'Our program is recognized by agricultural institutions worldwide.'
                    },
                    {
                        'icon': 'bi-tools',
                        'title': 'Practical Skills',
                        'description': 'Gain hands-on experience with modern agricultural techniques and technologies.'
                    },
                    {
                        'icon': 'bi-globe',
                        'title': 'Global Network',
                        'description': 'Connect with agricultural professionals and fellow students from around the world.'
                    },
                    {
                        'icon': 'bi-briefcase',
                        'title': 'Employment Opportunities',
                        'description': 'Our graduates are highly sought after by agricultural employers globally.'
                    }
                ]
            },
            'testimonials': {
                'title': 'Success Stories',
                'description': 'Hear from our alumni about their experiences with TAU Agrostudies',
                'items': [
                    {
                        'quote': 'The TAU Agrostudies program transformed my understanding of modern agriculture. The combination of theoretical knowledge and practical experience at my farm placement gave me the confidence to start my own agricultural business.',
                        'author': 'John Mwangi',
                        'position': 'Program Graduate, 2023',
                        'initials': 'JM'
                    },
                    {
                        'quote': 'As an international student, I was amazed by the support system at TAU Agrostudies. The mentors were always available to help, and the farm placement gave me practical skills I couldn\'t have learned in a classroom.',
                        'author': 'Lucia Nguyen',
                        'position': 'Current Student, Vietnam',
                        'initials': 'LN'
                    },
                    {
                        'quote': 'The connections I made through TAU Agrostudies have been invaluable. I now work as a farm manager implementing sustainable practices I learned during my training, and I regularly collaborate with fellow alumni on agricultural projects.',
                        'author': 'David Kimani',
                        'position': 'Farm Manager, Green Valley Farms',
                        'initials': 'DK'
                    }
                ]
            },
            'cta': {
                'title': 'Ready to Grow Your Agricultural Career?',
                'description': 'Join hundreds of students who have transformed their lives through the TAU Agrostudies program.'
            }
        }
    } 