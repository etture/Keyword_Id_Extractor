import subprocess as sp


def send_mail(recipient_list, subject_line, message, attachment_files):
    """
    Send the message with mutt
    """
    attachment_string = make_attachment_string(attachment_files)
    recipient_string = make_recipient_list_string(recipient_list)
    command = '''
mutt -s "{0}" {1} -- "{2}" <<E0F
"{3}"
E0F'''.format(subject_line, attachment_string, recipient_string, message)
    print('Email command is:\n{0}\n'.format(command))
    print('Running command, sending email...')
    subprocess_cmd(command)


def subprocess_cmd(command):
    """
    Runs a terminal command with stdout piping enabled
    """
    import subprocess as sp
    process = sp.Popen(command,stdout=sp.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    print(proc_stdout)


def make_attachment_string(attachment_files):
    """
    Return a string to use in the mutt command to include attachment files
    ex:
    -a "$attachment_file" -a "$summary_file" -a "$zipfile"
    """
    attachment_strings = []
    if len(attachment_files) > 0:
        for file in attachment_files:
            file_string = '-a "{0}" '.format(file)
            attachment_strings.append(file_string)
    attachment_string = ''.join(attachment_strings)
    return attachment_string


def make_recipient_list_string(recipient_list):
    """
    Return a string to use in the mutt command for specifying recipients
    """
    return ', '.join(recipient_list)


if __name__ == '__main__':
    sample_command = '''
mutt -s "subject" -a "./results/2019-4-4-11-12_맥북_50_np.txt" -a "./results/2019-4-4-11-12_맥북_50_total.txt" -- "etture+p1@gmail.com, etture+p2@gmfail.com" <<E0F
"message body"
E0F'''
    print(sp.Popen(sample_command, stdout=sp.PIPE, shell=True).communicate()[0].strip())
